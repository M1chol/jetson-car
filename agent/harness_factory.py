from __future__ import annotations

from typing import Any

from agent.function_harness import FunctionGemmaHarness
from agent.harness import CONFIG_PATH, AtomHarness, load_config


def create_harness(
    config_path: str | None = None,
    silent: bool = False,
) -> Any:
    resolved_config_path = config_path or CONFIG_PATH
    config = load_config(resolved_config_path)
    harness_type = config.get("harness_type", "prompt")

    if harness_type == "functiongemma":
        return FunctionGemmaHarness(
            config_path=resolved_config_path,
            silent=silent,
        )

    return AtomHarness(
        config_path=resolved_config_path,
        silent=silent,
    )
