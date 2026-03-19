from datetime import datetime
import inspect
from typing import Any, Callable, get_type_hints
from car.virtualGamepad import VirtualGamepad
import carSetup

_tools: dict[str, dict] = {}
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

        _tools[fn.__name__] = {
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
    gamepad = VirtualGamepad()
    status = carSetup.start(gamepad)
    return "Success" if status else "Failed"

@tool("Stop the car")
def stop_car() -> str:
    status = carSetup.stop()
    return "Success" if status else "Failed"                                                                                                                      return f"Error: {e}"

@tool("Set the steering angle")
def set_angle(angle: int) -> str:
    try:
        gamepad.currentAngle = angle
        return "Success"
    except:
        return "Unknown error"