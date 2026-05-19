from __future__ import annotations

import json
import os
from typing import Any, Callable

from ollama import Client

from agent.carSetup import steer
from agent.tools import (
    execute_registered_tool,
    get_ollama_tool_schemas,
    stop_car_abrupt,
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
CAMERA_TOOL_NAME = "analizuj_obraz_z_kamery"


def load_config(config_path: str = CONFIG_PATH) -> dict[str, Any]:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class FunctionGemmaHarness:
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
        self.model = model or config.get("function_ollama_model_name", "functiongemma")
        self.max_tool_rounds = max_tool_rounds
        self.silent = silent
        self.client = Client(host=self.ollama_host)
        self.tool_schemas = get_ollama_tool_schemas(exclude={CAMERA_TOOL_NAME})

    def system_message(self) -> dict[str, str]:
        return {
            "role": "developer",
            "content": (
                "You are a model that can do function calling with the following functions. "
                "Jestes asystentem Atom i sterujesz samochodem. "
                "Uzywaj funkcji tylko wtedy, gdy uzytkownik wyraznie prosi o "
                "akcje albo odczyt. Nie masz dostepu do kamery w tym trybie; "
                "jesli uzytkownik pyta o obraz z kamery, powiedz krotko, ze "
                "ten lekki model nie obsluguje analizy obrazu."
            ),
        }

    def ask(
        self,
        user_message: str,
        silent: bool | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> str:
        if silent is None:
            silent = self.silent

        messages: list[dict[str, Any]] = [
            self.system_message(),
            {"role": "user", "content": user_message},
        ]

        final_text = ""

        for _ in range(self.max_tool_rounds):
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=self.tool_schemas,
                stream=False,
            )
            message = get_value(response, "message", {})
            tool_calls = get_value(message, "tool_calls", None) or []
            content = (get_value(message, "content", "") or "").strip()

            if not tool_calls:
                final_text = content
                break

            messages.append(message)

            for tool_call in tool_calls:
                function = get_value(tool_call, "function", {})
                name = get_value(function, "name", "")
                args = get_value(function, "arguments", {}) or {}
                try:
                    result = execute_registered_tool(name, args)
                except Exception as e:
                    result = {
                        "ok": False,
                        "message": f"Blad podczas wykonywania funkcji {name}: {e}",
                    }
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
        else:
            final_text = "Przekroczono limit wywolan funkcji."

        if not silent and final_text:
            print(f"Atom: {final_text}")

        if on_text is not None and final_text:
            on_text(final_text)

        return final_text

    def check_connection(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as e:
            if not self.silent:
                print(f"Cannot reach Ollama: {e}")
            return False

    def cleanup(self) -> None:
        if steer:
            steer.stop()
        stop_car_abrupt()
