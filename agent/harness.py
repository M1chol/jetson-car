import json
import re
import os

from agent.tools import tools, stop_car_abrupt
from agent.carSetup import steer

from ollama import chat as ollama_chat, list as ollama_list


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, encoding="utf-8") as f:
    _config = json.load(f)

OLLAMA_HOST = _config.get("ollama_host", "http://localhost:11434")
MODEL = _config.get("ollama_model_name", "gemma3:4b")
MAX_TOOL_ROUNDS = 4

TOOL_FORMAT = """
<tool_call>
{{"name": "<tool_name>", "arguments": {{<key-value pairs as JSON>}}}}
</tool_call>
""".strip()


def build_system_prompt() -> str:
    tool_docs = []
    for name, meta in tools.items():
        param_lines = []
        for pname, pmeta in meta["parameters"].items():
            req = "required" if pmeta["required"] else "optional"
            param_lines.append(
                f"  - {pname} ({pmeta['type']}, {req}): {pmeta['description']}"
            )
        params_str = "\n".join(param_lines) if param_lines else "  (no parameters)"
        tool_docs.append(
            f"### {name}\n"
            f"Description: {meta['description']}\n"
            f"Parameters:\n{params_str}"
        )

    tools_block = "\n\n".join(tool_docs)

    return f"""You are a helpful assistant "Atom" with access to the following tools. You always respond in Polish
---
TOOLS
{tools_block}

---
If not directly asked, do not use tools
HOW TO USE A TOOL (ONLY WHEN ASKED)
To call a tool, output using this exact format:
<tool_call>
{{"name": "tool_name", "arguments": {{"param": "value"}}}}
</tool_call>

Rules:
- Only call one tool per response.
- After a <tool_result> is shown, continue your answer naturally.
- Never invent tool results; always wait for the actual result.
"""


TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL | re.IGNORECASE
)


def extract_tool_call(text: str) -> dict | None:
    match = TOOL_CALL_RE.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"[harness] Failed to parse tool call JSON: {e}")
        return None


def execute_tool(call: dict) -> str:
    name = call.get("name")
    args = call.get("arguments", {})

    if name not in tools:
        return f"Error: unknown tool '{name}'"

    fn = tools[name]["function"]
    try:
        result = fn(**args)
        return str(result)
    except TypeError as e:
        return f"Error calling '{name}': {e}"
    except Exception as e:
        return f"Error while executing '{name}': {e}"


def chat(messages: list[dict], silent: bool = False) -> str:
    """Stream a response from Ollama, printing tokens live. Returns full text."""
    chunks: list[str] = []

    if not silent:
        print("Atom: ", end="", flush=True)

    for part in ollama_chat(
        model=MODEL,
        messages=messages,
        stream=True,
        options={"host": OLLAMA_HOST},
    ):
        token = part["message"]["content"]
        chunks.append(token)
        if not silent:
            print(token, end="", flush=True)

    if not silent:
        print()

    return "".join(chunks)


def run_agent(user_message: str, silent: bool = False) -> str:
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_message},
    ]

    last_response = ""

    for round_num in range(MAX_TOOL_ROUNDS):
        if not silent:
            print(f"[harness] Round {round_num + 1} — calling model...")

        response = chat(messages, silent=silent)
        last_response = response

        call = extract_tool_call(response)
        if call is None:
            return response

        tool_name = call.get("name", "?")
        if not silent:
            print(
                f"\n[harness] Executing tool: "
                f"{tool_name}({call.get('arguments', {})})"
            )

        result = execute_tool(call)

        if not silent:
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

    print("[harness] Max tool rounds reached without a final answer.")
    return last_response


def main():
    try:
        ollama_list()
    except ConnectionError as e:
        print(f"Cannot reach Ollama: {e}")
        return

    print("Atom Agent Harness\n")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            if steer:
                steer.stop()
            stop_car_abrupt()
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            if steer:
                steer.stop()
            stop_car_abrupt()
            print("Goodbye!")
            break

        run_agent(user_input)
        print()


if __name__ == "__main__":
    main()