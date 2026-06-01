# Research: Ask Layer Structured Fallback

## Decision: Treat LLM connection failure as an operational blocker

**Rationale**: `/ask` layer depends on the LLM for tool planning and interpretation. When the configured endpoint refuses connections and no tool evidence exists, continuing into Pydantic extraction only produces misleading schema errors.

**Alternatives considered**: Return a low-confidence default layer. Rejected because it would let downstream nodes diagnose without evidence and could trigger misleading repair advice.

## Decision: Enable text JSON fallback only for layer extraction

**Rationale**: Local OpenAI-compatible gateways may not support native structured output, while still supporting normal chat completion. Enabling `allow_text_fallback=True` keeps Pydantic validation but removes the native-structured hard dependency.

**Alternatives considered**: Disable Pydantic entirely. Rejected because the validated `LayerOutput` contract is the handoff boundary for downstream nodes.

## Decision: Preserve `/query` direct path

**Rationale**: `/query` already has a direct JSON/tool-result path to avoid slow extra structured extraction. This feature must not undo that performance fix.

**Alternatives considered**: Apply the fallback globally. Rejected because `/query` has separate success criteria and has already been optimized.
