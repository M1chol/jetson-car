import time
import sys
import json
import re
from agent.stt import sttWrapper
from agent.tts import ttsWrapper
import agent.harness as harness
from ollama import chat as ollama_chat

# Configuration for start.py
CONFIG_PATH = "agent/config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

config = load_config()
MODEL = config.get("ollama_model_name", "gemma3:4b")
OLLAMA_HOST = config.get("ollama_host", "http://localhost:11434")

def chat_with_tts(messages: list[dict], tts: ttsWrapper) -> str:
    """Stream a response from Ollama and feed it to TTS."""
    chunks: list[str] = []
    print("Atom: ", end="", flush=True)

    for part in ollama_chat(
        model=MODEL,
        messages=messages,
        stream=True,
        options={"host": OLLAMA_HOST},
    ):
        token = part["message"]["content"]
        chunks.append(token)
        print(token, end="", flush=True)
        tts.speak(token)

    print()
    # Signal end of speaking (some TTS implementations use None to flush)
    tts.speak(None)
    return "".join(chunks)

def run_agent_voice(user_message: str, tts: ttsWrapper) -> None:
    messages = [
        {"role": "system", "content": harness.build_system_prompt()},
        {"role": "user", "content": user_message},
    ]

    for round_num in range(harness.MAX_TOOL_ROUNDS):
        response = chat_with_tts(messages, tts)

        call = harness.extract_tool_call(response)
        if call is None:
            return

        tool_name = call.get("name", "?")
        print(f"\n[harness] Executing tool: {tool_name}({call.get('arguments', {})})")
        result = harness.execute_tool(call)
        print(f"[harness] Tool result: {result}\n")

        messages.append({"role": "assistant", "content": response})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"<tool_result>\n"
                    f"{{\n"
                    f'  "name": "{tool_name}",\n'
                    f'  "result": {json.dumps(result)}\n'
                    f"}}\n"
                    f"</tool_result>\n\n"
                    f"Continue your response using the tool result above."
                ),
            }
        )

def main():
    print("Initializing TTS and STT...")
    tts = ttsWrapper()
    
    _state = {"text": "", "ready": False}

    def stt_callback(text, is_final):
        if is_final:
            _state["text"] = text
            _state["ready"] = True
            print(f"\n[User]: {text}")
        else:
            sys.stdout.write(f"\r[Listening...]: {text}")
            sys.stdout.flush()

    stt = sttWrapper(stt_callback)
    
    print("Atom Voice Agent Ready. Speak Polish to interact.")
    
    try:
        while True:
            if _state["ready"]:
                user_msg = _state["text"]
                _state["ready"] = False
                _state["text"] = ""
                
                run_agent_voice(user_msg, tts)
                print("\n[Waiting for speech...]")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()
