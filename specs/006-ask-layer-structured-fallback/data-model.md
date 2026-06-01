# Data Model: Ask Layer Structured Fallback

## Layer Extraction Attempt

- `question`: user question being diagnosed
- `full_analysis_text`: text and tool evidence collected by layer stage 1
- `failure_reason`: explanation passed into the extraction prompt
- `allow_text_fallback`: whether normal JSON prompt fallback is permitted after native structured failure

## LLM Unavailable Signal

- `stage1_text`: synthetic agent failure text such as `Agent 执行异常: Connection error.`
- `successful_tool_events`: count of successful tool results collected before the failure
- `message`: user-facing operational error that identifies LLM connectivity as the blocker

## Validated LayerOutput

- Existing `LayerOutput` schema
- Must include `layer`, `confidence`, and `reasoning`
- May include `abnormal_pods`, `pod_status_keyword`, `pod_abnormal_type`, and `full_analysis`
