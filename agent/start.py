import threading
import time

from agent.harness import AtomHarness
from agent.stt import sttWrapper


class VoiceApp:
    def __init__(self) -> None:
        self.harness = AtomHarness(silent=True)
        self.stop_event = threading.Event()
        self.is_processing = False

    def on_speech(self, text: str, is_final: bool) -> None:
        text = text.strip()
        if not text:
            return

        if not is_final:
            print(f"\r[partial] {text}", end="", flush=True)
            return

        print(f"\n[final] {text}")

        if text.lower() in {"quit", "exit", "stop program", "zakończ", "wyjdz"}:
            print("[main] Exit command received.")
            self.stop_event.set()
            return

        if self.is_processing:
            print("[main] Still processing previous command, ignoring.")
            return

        self.is_processing = True
        try:
            response = self.harness.ask(text, silent=False)
            print(f"\n[main] Final response: {response}\n")
        except Exception as e:
            print(f"[main] Error while processing speech: {e}")
        finally:
            self.is_processing = False

    def run(self) -> None:
        if not self.harness.check_connection():
            return

        print("Voice control started.")
        print("Speak a command.")
        print("Say 'quit' or 'exit' to stop.\n")

        stt = sttWrapper(self.on_speech)

        try:
            while not self.stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[main] Keyboard interrupt received.")
        finally:
            self.stop_event.set()
            self.harness.cleanup()

            try:
                del stt
            except Exception:
                pass

            print("[main] Goodbye!")


def main() -> None:
    app = VoiceApp()
    app.run()


if __name__ == "__main__":
    main()
