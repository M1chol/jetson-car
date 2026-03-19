from harness import tool
from datetime import datetime

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

