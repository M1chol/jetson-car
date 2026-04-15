import os
import json
import threading
from queue import Empty, Queue

import numpy as np
import re
import sounddevice as sd
from piper.config import SynthesisConfig
from piper.voice import PiperVoice


class ttsWrapper:
    def __init__(self) -> None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, encoding="utf-8") as f:
            self.__config = json.load(f)["tts_config"]

        if not self.__config:
            raise FileNotFoundError("config file not found")

        self.__model_path = os.path.join(
            os.path.dirname(__file__),
            self.__config["model_dir"],
            self.__config["model"] + ".onnx",
        )

        self.__voice = PiperVoice.load(self.__model_path)
        self.__syn_config = SynthesisConfig(
            length_scale=self.__config["length_scale"],
            noise_scale=self.__config["noise_scale"],
            noise_w_scale=self.__config["noise_w_scale"],
            volume=self.__config["volume"],
        )
        self.__stream = sd.OutputStream(
            samplerate=self.__voice.config.sample_rate,
            channels=1,
            dtype="int16",
            latency="high",
            blocksize=self.__config["blocksize"],
            callback=self.callback,
        )
        self.__audio_queue = Queue(maxsize=self.__config["buffersize"])
        self.__text_queue = Queue()
        self.__leftover = np.empty((0, 1), dtype=np.int16)
        self.__audio_thread = threading.Thread(target=self.__worker, daemon=True)
        self.__audio_thread_stop_event = threading.Event()
        self.__interrupt_event = threading.Event()
        self.__state_lock = threading.Lock()

        self.__stream.start()
        self.__audio_thread.start()

    def __del__(self):
        self.close()

    def close(self) -> None:
        self.stop()

        try:
            self.__audio_thread_stop_event.set()
        except Exception:
            pass

        try:
            self.__text_queue.put_nowait(None)
        except Exception:
            pass

        try:
            self.__stream.stop()
        except Exception:
            pass

        try:
            self.__stream.close()
        except Exception:
            pass

    def callback(self, outdata, frames, time, status):
        wrote = 0

        def copy_from(src):
            nonlocal wrote
            if src.size == 0:
                return 0
            take = min(len(src), frames - wrote)
            outdata[wrote : wrote + take] = src[:take]
            wrote += take
            return take

        if len(self.__leftover) > 0 and wrote < frames:
            taken = copy_from(self.__leftover)
            if taken < len(self.__leftover):
                self.__leftover = self.__leftover[taken:]
            else:
                self.__leftover = self.__leftover[0:0]

        while wrote < frames:
            try:
                data = self.__audio_queue.get_nowait()
            except Empty:
                outdata[wrote:frames] = 0
                return

            data = data.reshape(-1, 1)
            if data.size == 0:
                continue

            taken = copy_from(data)
            if taken < len(data):
                self.__leftover = data[taken:]
                return

    def __clear_queue(self, queue: Queue) -> None:
        while True:
            try:
                queue.get_nowait()
            except Empty:
                return

    def __push_text(self, text: str) -> None:
        if not text.strip():
            return

        for audio_chunk in self.__voice.synthesize(
            text, syn_config=self.__syn_config
        ):
            if self.__interrupt_event.is_set():
                return
            audio_bytes = audio_chunk.audio_int16_array
            self.__audio_queue.put(audio_bytes)

    def __worker(self):
        while not self.__audio_thread_stop_event.is_set():
            sentence = self.__text_queue.get()
            if sentence is None:
                continue

            self.__push_text(sentence)

    def stop(self) -> None:
        self.__interrupt_event.set()
        with self.__state_lock:
            self.__clear_queue(self.__text_queue)
            self.__clear_queue(self.__audio_queue)
            self.__leftover = self.__leftover[0:0]

    def speak(self, text: str | None):
        if not text:
            return

        pattern = r"[^a-zA-Z0-9ąćęłńóśźżĄĆĘŁŃÓŚŹŻ.,!?;:()\"' \-]+"
        sanitized = re.sub(pattern, "", text).strip()
        if sanitized:
            self.__interrupt_event.clear()
            self.__text_queue.put(sanitized)
