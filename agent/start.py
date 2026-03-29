import os
import sys
import time
import json

from agent.stt import sttWrapper
from agent.tts import ttsWrapper
import agent.harness as harness


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    load_config()

    try:
        harness.ollama_list()
    except ConnectionError as e:
        print(f"Cannot reach Ollama: {e}")
        return

    print("Initializing TTS and STT...")
    tts = ttsWrapper()

    state = {
        "text": "",
        "ready": False,
    }

    def stt_callback(text, is_final):
        clean = text.strip()
        if not clean:
            return

        if is_final:
            state["text"] = clean
            state["ready"] = True
            sys.stdout.write("\r" + " " * 120 + "\r")
            print(f"Ty: {clean}")
        else:
            sys.stdout.write(f"\rNasłuch: {clean}")
            sys.stdout.flush()

    stt = sttWrapper(stt_callback)

    print("Atom Voice Agent Ready. Speak Polish to interact.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            if state["ready"]:
                user_msg = state["text"]
                state["ready"] = False
                state["text"] = ""

                response = harness.run_agent(user_msg, silent=False)

                if response:
                    tts.speak(response)
                    tts.speak(None)

                print("\n[Waiting for speech...]")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        try:
            if harness.steer:
                harness.steer.stop()
        except Exception:
            pass

        try:
            harness.stop_car_abrupt()
        except Exception:
            pass

        del stt
        del tts


if __name__ == "__main__":
    main()