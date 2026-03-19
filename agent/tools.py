from datetime import datetime
import inspect
from typing import Any, Callable, get_type_hints

_tools: dict[str, dict] = {}

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


@tool("Perform basic arithmetic: add, subtract, multiply, divide")
def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "Error: only basic arithmetic is allowed"
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:                                                                                                                           return f"Error: {e}"

