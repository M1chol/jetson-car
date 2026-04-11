from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any, Callable, get_type_hints

import agent.carSetup as carSetup
from car.virtualGamepad import VirtualGamepad

tools: dict[str, dict[str, Any]] = {}
gamepad: VirtualGamepad | None = None


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
            "Samochód nie jest uruchomiony. Najpierw użyj narzędzia "
            "'uruchom_samochod'."
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
        "Uruchamia kontroler samochodu i przygotowuje pojazd do jazdy. "
        "Tego narzędzia należy użyć przed ustawianiem skrętu lub prędkości."
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
        "Ustawia prędkość samochodu jako liczbę całkowitą odpowiednią dla "
        "aktualnego systemu sterowania."
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
