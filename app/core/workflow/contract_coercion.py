"""Shape-only coercion shared by stage output contracts.

Models often answer a list-of-text field with one string (``"unresolved": "x"``).
The meaning is unambiguous, so the contract accepts it as a one-item list instead
of spending a structured retry on it (live: "unresolved: Input should be a valid
list" in most deep runs). Content is never rewritten; an empty string is no item.
"""

import json
from typing import Any

from pydantic import BeforeValidator


def text_items(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return value


TextItems = BeforeValidator(text_items)


def json_items(value: Any) -> Any:
    """A list of objects sent as its JSON text (live: "key_facts: Input should be a valid list")."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return value  # not JSON: let validation report it
        return parsed if isinstance(parsed, list) else value
    return value


JsonItems = BeforeValidator(json_items)
