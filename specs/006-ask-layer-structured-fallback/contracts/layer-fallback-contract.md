# Contract: Ask Layer Structured Fallback

## Layer Extraction Call

When `/ask` layer needs structured finalization, it calls `AICall.call_structured` with:

```json
{
  "schema": "LayerOutput",
  "node_id": "layer_extract",
  "allow_text_fallback": true
}
```

## Unavailable LLM Error

When layer stage 1 returns only a synthetic LLM connection failure and no successful tool evidence, the workflow raises an error containing:

```text
LLM 服务不可用
```

The message should include the original connection failure text when available.

## Non-Goals

- Do not generate a fallback repair plan.
- Do not return a fake layer when all LLM calls fail.
- Do not change query direct rendering.
