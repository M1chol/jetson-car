import threading
import time
import re

from agent.harness_factory import create_harness
from agent.stt import sttWrapper
from agent.tts import ttsWrapper


SENTENCE_END_RE = re.compile(r"(.+?[.!?]+(?:[\"')\\]]+)?)(?:\s+|$)", re.DOTALL)


class SentenceStreamer:
    def __init__(self, tts: ttsWrapper) -> None:
        self.tts = tts
        self.buffer = ""
        self.is_displaying = False

    def push(self, chunk: str) -> None:
        if not chunk:
            return

        if not self.is_displaying:
            print("Atom: ", end="", flush=True)
            self.is_displaying = True

        print(chunk, end="", flush=True)
        self.buffer += chunk
        self.__emit_complete_sentences()

    def flush(self) -> None:
        remainder = self.buffer.strip()
        self.buffer = ""
        if remainder:
            self.tts.speak(remainder)
        if self.is_displaying:
            print()
            self.is_displaying = False

    def reset(self) -> None:
        self.buffer = ""
        self.is_displaying = False

    def __emit_complete_sentences(self) -> None:
        while True:
            match = SENTENCE_END_RE.match(self.buffer)
            if not match:
                return

            sentence = match.group(1).strip()
            self.buffer = self.buffer[match.end():]
            if sentence:
                self.tts.speak(sentence)


class VoiceApp:
    def __init__(self) -> None:
        self.harness = create_harness(silent=True)
        self.tts = ttsWrapper()
        self.tts_streamer = SentenceStreamer(self.tts)
        self.stop_event = threading.Event()
        self.is_processing = False

    def on_speech(self, text: str, is_final: bool) -> None:
        text = text.strip()
        if not text:
            return

        if not is_final:
            if not self.is_processing:
                self.tts.stop()
            print(f"\rYou: {text}", end="", flush=True)
            return

        print(f"\rYou: {text}")

        if text.lower() in {"quit", "exit", "stop program", "zakończ", "wyjdz"}:
            self.stop_event.set()
            return

        if self.is_processing:
            return

        self.is_processing = True
        try:
            self.tts_streamer.reset()
            self.harness.ask(
                text,
                silent=True,
                on_text=self.tts_streamer.push,
            )
            self.tts_streamer.flush()
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            self.is_processing = False

    def run(self) -> None:
        if not self.harness.check_connection():
            return

        print("Voice control started. Say 'quit' or 'exit' to stop.\n")

        stt = sttWrapper(self.on_speech)

        try:
            while not self.stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print()
        finally:
            self.stop_event.set()
            self.harness.cleanup()
            self.tts.close()

            try:
                del stt
            except Exception:
                pass

            print("Goodbye!")


def main() -> None:
    app = VoiceApp()
    app.run()


if __name__ == "__main__":
    main()
