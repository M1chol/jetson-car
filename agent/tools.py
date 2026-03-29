from datetime import datetime
import inspect
from typing import Any, Callable, get_type_hints
from car.virtualGamepad import VirtualGamepad
import agent.carSetup as carSetup
from threading import Event
import json

tools: dict[str, dict] = {}
gamepad = None

def tool(description: str):
    """Decorator to register a function as a callable tool."""

    def decorator(fn: Callable):
        hints = get_type_hints(fn)
        sig = inspect.signature(fn)

        params = {}
        for name, param in sig.parameters.items():
            hint = hints.get(name, str)
            type_map = {
                int: "integer",
                float: "number",
                bool: "boolean",
                str: "string",
            }
            params[name] = {
                "type": type_map.get(hint, "string"),
                "description": f"Parameter '{name}'",
                "required": param.default is inspect.Parameter.empty,
            }

        tools[fn.__name__] = {
            "function": fn,
            "description": description,
            "parameters": params,
        }
        return fn

    return decorator

@tool("Get the current date and time")
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool("Initialize the car")
def start_car() -> str:
    global gamepad
    with open("car/config.json") as file:
        config = json.load(file)
        if not config:
            print("Config file failed to load")
            quit()
    # car Setup will quit if failed
    gamepad = carSetup.start(gamepad)
    return "Success"

@tool("Stop the car")
def stop_car() -> str:
    status = carSetup.stop()
    return "Success" if status else "Failed"

@tool("Set the steering angle")
def set_angle(angle: int) -> str:
    try:
        gamepad.currentAngle = angle
        return "Success"
    except:
        return "Unknown error"

def stop_car_abrupt() -> None:
    carSetup.stop()
