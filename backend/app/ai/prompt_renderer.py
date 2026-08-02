"""Prompt template rendering and variable validation."""

from __future__ import annotations

import re
from typing import Any

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class PromptRenderError(ValueError):
    """Raised when template variables are missing or invalid."""


def extract_variables(*templates: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for template in templates:
        for match in VARIABLE_PATTERN.finditer(template or ""):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                found.append(name)
    return found


def validate_declared_variables(
    declared: list[str],
    *templates: str,
) -> None:
    """Ensure declared variables cover every placeholder in templates."""
    used = set(extract_variables(*templates))
    declared_set = {item.strip() for item in declared if item and item.strip()}
    missing = sorted(used - declared_set)
    if missing:
        raise PromptRenderError("Undeclared template variables: " + ", ".join(missing))
    empty = [item for item in declared if not str(item).strip()]
    if empty:
        raise PromptRenderError("Variable names must not be empty.")


def render_template(template: str, variables: dict[str, Any]) -> str:
    """Replace ``{{var}}`` placeholders. Missing keys raise PromptRenderError."""

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise PromptRenderError(f"Missing value for variable '{key}'.")
        value = variables[key]
        return "" if value is None else str(value)

    return VARIABLE_PATTERN.sub(replacer, template or "")
