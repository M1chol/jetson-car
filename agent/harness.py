import json
import re
from tools import _tools
from carSetup import steering

from ollama import chat as ollama_chat, list as ollama_list

OLLAMA_HOST = "http://localhost:11434"
MODEL = "gemma3n:e2b"
MAX_TOOL_ROUNDS = 4

TOOL_FORMAT = """
<tool_call>
{{"name": "<tool_name>", "arguments": {{<key-value pairs as JSON>}}}}
</tool_call>
""".strip()

def build_system_prompt() -> str:
    tool_docs = []
    for name, meta in _tools.items():
        param_lines = []
        for pname, pmeta in meta["parameters"].items():
            req = "required" if pmeta["required"] else "optional"
            param_lines.append(
                f"  - {pname} ({pmeta['type']}, {req}): {pmeta['description']}"
            )
        params_str = (
            "\n".join(param_lines) if param_lines else "  (no parameters)"
        )
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
HOW TO USE A TOOL
When you need to call a tool, output it on its own line using this exact format:
<tool_call>
{{"name": "tool_name", "arguments": {{"param": "value"}}}}
</tool_call>

Rules:
- Only call one tool per response.
- After a <tool_result> is shown, continue your answer naturally.
- If no tool is needed, just answer directly.
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

    if name not in _tools:
        return f"Error: unknown tool '{name}'"

    fn = _tools[name]["function"]
    try:
        result = fn(**args)
        return str(result)
    except TypeError as e:
        return f"Error calling '{name}': {e}"


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
        print()  # newline after streamed response

    return "".join(chunks)


def run_agent(user_message: str) -> None:
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_message},
    ]

    for round_num in range(MAX_TOOL_ROUNDS):
        print(f"[harness] Round {round_num + 1} — calling model...")
        response = chat(messages)

        call = extract_tool_call(response)
        if call is None:
            # No tool call — streamed final answer already printed
            return

        tool_name = call.get("name", "?")
        print(
            f"\n[harness] Executing tool: "
            f"{tool_name}({call.get('arguments', {})})"
        )
        result = execute_tool(call)
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
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            steering.stop()
            print("Goodbye!")
            break

        run_agent(user_input)
        print()


if __name__ == "__main__":
    main()
