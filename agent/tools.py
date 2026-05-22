from __future__ import annotations

import inspect
import json
import os
from datetime import datetime
from typing import Any, Callable, get_type_hints

from ollama import Client

import agent.carSetup as carSetup
from agent.camera import capture_jpeg_frame
from car.virtualGamepad import VirtualGamepad

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
tools: dict[str, dict[str, Any]] = {}
gamepad: VirtualGamepad | None = None


def load_agent_config() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_ollama_tool_schemas(exclude: set[str] | None = None) -> list[dict[str, Any]]:
    exclude = exclude or set()
    schemas = []

    for name, meta in tools.items():
        if name in exclude:
            continue

        properties = {}
        required = []

        for param_name, param_meta in meta["parameters"].items():
            properties[param_name] = {
                "type": param_meta["type"],
                "description": param_meta["description"],
            }
            if param_meta["required"]:
                required.append(param_name)

        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            }
        )

    return schemas


def execute_registered_tool(name: str, args: dict[str, Any] | None = None) -> Any:
    if name not in tools:
        return {
            "ok": False,
            "message": f"Nieznana funkcja: {name}",
        }

    return tools[name]["function"](**(args or {}))


def tool(
    description: str,
    parameter_descriptions: dict[str, str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    parameter_descriptions = parameter_descriptions or {}

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        hints = get_type_hints(fn)
        sig = inspect.signature(fn)

        params: dict[str, dict[str, Any]] = {}
        type_map = {
            int: "integer",
            float: "number",
            bool: "boolean",
            str: "string",
        }

        for name, param in sig.parameters.items():
            hint = hints.get(name, str)

            params[name] = {
                "type": type_map.get(hint, "string"),
                "description": parameter_descriptions.get(
                    name, f"Parametr '{name}'"
                ),
                "required": param.default is inspect.Parameter.empty,
            }

        tools[fn.__name__] = {
            "function": fn,
            "description": description,
            "parameters": params,
        }

        return fn

    return decorator


def require_gamepad() -> VirtualGamepad:
    if gamepad is None:
        raise RuntimeError(
            "Samochód nie jest uruchominy"
        )
    return gamepad


@tool(
    description="Pobiera aktualną lokalną datę i godzinę.",
)
def pobierz_aktualny_czas() -> dict[str, Any]:
    return {
        "ok": True,
        "message": "Pobrano aktualny czas.",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@tool(
    description=(
        "Robi pojedyncze zdjecie z kamery samochodu, wysyla je do modelu Gemma "
        "i zwraca opis tego, co widac. Uzyj tylko gdy uzytkownik poprosi o "
        "sprawdzenie obrazu, kamery albo otoczenia."
    ),
)
def analizuj_obraz_z_kamery() -> dict[str, Any]:
    try:
        config = load_agent_config()
        camera_config = config.get("camera_config", {})
        frame = capture_jpeg_frame(
            pipeline=camera_config.get("pipeline", ""),
            warmup_frames=int(camera_config.get("warmup_frames", 0)),
            jpeg_quality=int(camera_config.get("jpeg_quality", 90)),
        )

        prompt = camera_config.get(
            "analysis_prompt",
            "Opisz krotko, co widzisz na obrazie z kamery samochodu.",
        )
        client = Client(host=config.get("ollama_host", "http://localhost:11434"))
        response = client.chat(
            model=config.get("ollama_model_name", "gemma3:4b"),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [frame.jpeg_bytes],
                }
            ],
        )

        description = response["message"]["content"].strip()
        return {
            "ok": True,
            "message": "Przeanalizowano obraz z kamery.",
            "description": description,
            "image": {
                "width": frame.width,
                "height": frame.height,
                "saved_path": frame.saved_path,
            },
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Nie udalo sie przeanalizowac obrazu z kamery: {e}",
        }


@tool(
    description=(
        "Uruchamia kontroler samochodu i przygotowuje pojazd do jazdy. "
    ),
)
def uruchom_samochod() -> dict[str, Any]:
    global gamepad

    try:
        gamepad = carSetup.start()
        return {
            "ok": True,
            "message": "Samochód został uruchomiony.",
        }
    except Exception as e:
        gamepad = None
        return {
            "ok": False,
            "message": f"Nie udało się uruchomić samochodu: {e}",
        }


@tool(
    description="Zatrzymuje samochód w normalny sposób.",
)
def zatrzymaj_samochod() -> dict[str, Any]:
    global gamepad

    try:
        status = carSetup.stop()
        if status:
            gamepad = None
            return {
                "ok": True,
                "message": "Samochód został zatrzymany.",
            }

        return {
            "ok": False,
            "message": "Nie udało się zatrzymać samochodu.",
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Błąd podczas zatrzymywania samochodu: {e}",
        }


@tool(
    description=(
        "Ustawia kąt skrętu samochodu. "
        "Wartości ujemne oznaczają skręt w lewo, dodatnie w prawo, a 0 "
        "ustawia koła na wprost."
    ),
    parameter_descriptions={
        "angle": (
            "Kąt skrętu jako liczba całkowita. "
            "Wartość ujemna oznacza lewo, dodatnia prawo, a 0 środek."
        ),
    },
)
def ustaw_kat(angle: int) -> dict[str, Any]:
    try:
        pad = require_gamepad()
        pad.currentAngle = angle
        return {
            "ok": True,
            "message": f"Ustawiono kąt skrętu na {angle}.",
            "angle": angle,
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Nie udało się ustawić kąta skrętu: {e}",
        }


@tool(
    description=(
        "Ustawia prędkość samochodu jako liczbę całkowitą "
    ),
    parameter_descriptions={
        "speed": "Docelowa prędkość jako liczba całkowita.",
    },
)
def ustaw_predkosc(speed: int) -> dict[str, Any]:
    try:
        pad = require_gamepad()
        pad.currentSpeed = speed
        return {
            "ok": True,
            "message": f"Ustawiono prędkość na {speed}.",
            "speed": speed,
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Nie udało się ustawić prędkości: {e}",
        }


def stop_car_abrupt() -> None:
    global gamepad
    carSetup.stop()
    gamepad = None
