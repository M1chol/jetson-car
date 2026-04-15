import json
import os
import re
from typing import Any, Callable

from ollama import chat as ollama_chat, list as ollama_list

from agent.carSetup import steer
from agent.tools import stop_car_abrupt, tools

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL | re.IGNORECASE
)


def load_config(config_path: str = CONFIG_PATH) -> dict[str, Any]:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


class AtomHarness:
    def __init__(
        self,
        config_path: str = CONFIG_PATH,
        ollama_host: str | None = None,
        model: str | None = None,
        max_tool_rounds: int = 4,
        silent: bool = False,
    ) -> None:
        config = load_config(config_path)

        self.ollama_host = ollama_host or config.get(
            "ollama_host", "http://localhost:11434"
        )
        self.model = model or config.get("ollama_model_name", "gemma3:4b")
        self.max_tool_rounds = max_tool_rounds
        self.silent = silent

    def build_system_prompt(self) -> str:
        tool_docs = []

        for name, meta in tools.items():
            param_lines = []
            for pname, pmeta in meta["parameters"].items():
                req = "required" if pmeta["required"] else "optional"
                param_lines.append(
                    f"  - {pname} ({pmeta['type']}, {req}): "
                    f"{pmeta['description']}"
                )

            params_str = "\n".join(param_lines) if param_lines else "  (no parameters)"
            tool_docs.append(
                f"### {name}\n"
                f"Description: {meta['description']}\n"
                f"Parameters:\n{params_str}"
            )

        tools_block = "\n\n".join(tool_docs)

        return f"""Jesteś asystentem Atom, sterujesz samochodem. Potrafisz wywoływać funkcję

---

- Jeżeli w popszedniej wiadomości jest  <tool_result> opisz krótko rezultat funkcji
- Nie wywołuj funkcji samodzielnie
- Nie wywołuj funkcji nieproszony

JAK UŻYWAĆ FUNCKJI
Aby wywołać funkcje odpowiedz wiadomościa w takim formacie:
<tool_call>
{{"name": "tool_name", "arguments": {{"param": "value"}}}}
</tool_call>

---

{tools_block}

"""

    def extract_tool_call(self, text: str) -> dict | None:
        match = TOOL_CALL_RE.search(text)
        if not match:
            return None

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            if not self.silent:
                print(f"[harness] Failed to parse tool call JSON: {e}")
            return None

    def execute_tool(self, call: dict) -> str:
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

    def chat(self, messages: list[dict], silent: bool | None = None) -> str:
        if silent is None:
            silent = self.silent

        chunks: list[str] = []

        if not silent:
            print("Atom: ", end="", flush=True)

        for part in ollama_chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={"host": self.ollama_host},
        ):
            token = part["message"]["content"]
            chunks.append(token)

            if not silent:
                print(token, end="", flush=True)

        if not silent:
            print()

        return "".join(chunks)

    def stream_chat(
        self,
        messages: list[dict],
        silent: bool | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> str:
        if silent is None:
            silent = self.silent

        chunks: list[str] = []
        mode = "undecided"
        tool_prefix = "<tool_call>"
        displayed_prefix = False

        def emit_text(text: str) -> None:
            nonlocal displayed_prefix
            if not text:
                return

            if not silent:
                if not displayed_prefix:
                    print("Atom: ", end="", flush=True)
                    displayed_prefix = True
                print(text, end="", flush=True)

            if on_text is not None:
                on_text(text)

        for part in ollama_chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={"host": self.ollama_host},
        ):
            token = part["message"]["content"]
            chunks.append(token)

            if mode == "text":
                emit_text(token)
                continue

            candidate = "".join(chunks).lstrip()
            lowered = candidate.lower()

            if not lowered:
                continue

            if lowered.startswith(tool_prefix):
                mode = "tool"
                continue

            if tool_prefix.startswith(lowered):
                continue

            mode = "text"
            emit_text(candidate)

        if mode == "undecided":
            candidate = "".join(chunks).lstrip()
            if candidate:
                mode = "text"
                emit_text(candidate)

        if not silent and displayed_prefix:
            print()

        return "".join(chunks)

    def ask(
        self,
        user_message: str,
        silent: bool | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> str:
        if silent is None:
            silent = self.silent

        messages = [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": user_message},
        ]

        last_response = ""

        for _ in range(self.max_tool_rounds):
            response = self.stream_chat(
                messages,
                silent=silent,
                on_text=on_text,
            )
            last_response = response

            call = self.extract_tool_call(response)
            if call is None:
                return response

            tool_name = call.get("name", "?")

            result = self.execute_tool(call)

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

        return last_response

    def check_connection(self) -> bool:
        try:
            ollama_list()
            return True
        except ConnectionError as e:
            if not self.silent:
                print(f"Cannot reach Ollama: {e}")
            return False

    def cleanup(self) -> None:
        if steer:
            steer.stop()
        stop_car_abrupt()


def main() -> None:
    harness = AtomHarness()

    if not harness.check_connection():
        return

    print("Atom Agent Harness\n")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            harness.cleanup()
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            harness.cleanup()
            print("Goodbye!")
            break

        harness.ask(user_input)
        print()


if __name__ == "__main__":
    main()
