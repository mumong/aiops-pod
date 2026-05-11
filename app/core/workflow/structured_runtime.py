"""Shared structured-agent runtime helpers for workflow nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass(frozen=True)
class StructuredAgentSpec:
    node_id: str
    output_schema: type[BaseModel]
    use_tools: bool = True
    allow_fallback: bool = True


class StructuredAgentRuntime:
    """Node-agnostic helpers for LangChain agent structured_response."""

    @staticmethod
    def extract_structured_response(response: Any, schema: type[SchemaT]) -> Optional[SchemaT]:
        structured = getattr(response, "structured_response", None)
        if structured is None:
            return None
        if isinstance(structured, schema):
            return structured
        if isinstance(structured, dict):
            return schema.model_validate(structured)
        if hasattr(structured, "model_dump"):
            return schema.model_validate(structured.model_dump())
        return None
