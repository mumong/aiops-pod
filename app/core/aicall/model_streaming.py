"""Preserve provider-visible reasoning, and hand it back inside a tool loop.

Reasoning models keep their plan in the reasoning channel. Qwen3's chat
template renders the reasoning of assistant turns that follow the last user
message (the current tool loop) and drops it for earlier turns; langchain-openai
never sends it, so the model saw every one of its own in-loop turns as an empty
think block followed by a tool call and, in live runs (66662a8287ce4dac,
ba91d54860594961), re-issued the previous call while its new reasoning planned a
different one. ``history_reasoning_field`` names the request field the serving
stack reads (vLLM 0.19 + Qwen3.6: ``reasoning``; older Qwen3 templates:
``reasoning_content``); empty keeps requests unchanged, which providers that
reject the field (DeepSeek) need.
"""

from typing import Any

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI


def feed_back_history_reasoning(messages: list, payload_messages: list, field: str) -> int:
    """Attach each in-loop assistant message's reasoning to its request dict.

    Only assistant turns after the last user message carry it (the template
    ignores earlier ones anyway). Returns how many dicts were annotated.
    """
    if not field or len(messages) != len(payload_messages):
        return 0
    last_user = -1
    for index, item in enumerate(payload_messages):
        if isinstance(item, dict) and item.get("role") == "user":
            last_user = index
    annotated = 0
    for index in range(last_user + 1, len(messages)):
        message, item = messages[index], payload_messages[index]
        if not isinstance(message, AIMessage) or not isinstance(item, dict):
            continue
        extra = message.additional_kwargs or {}
        reasoning = extra.get("reasoning_content") or extra.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            item[field] = reasoning
            annotated += 1
    return annotated


class VisibleChatOpenAI(ChatOpenAI):
    history_reasoning_field: str = ""

    def _get_request_payload(self, input_: Any, *, stop: Any = None, **kwargs: Any) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        if self.history_reasoning_field and isinstance(payload.get("messages"), list):
            messages = self._convert_input(input_).to_messages()
            feed_back_history_reasoning(
                messages, payload["messages"], self.history_reasoning_field
            )
        return payload

    def _convert_chunk_to_generation_chunk(self, chunk, default_chunk_class, base_generation_info):
        result = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        choices = chunk.get("choices") or []
        if result is not None and choices:
            delta = choices[0].get("delta") or {}
            for key in ("reasoning_content", "reasoning"):
                if isinstance(delta.get(key), str):
                    result.message.additional_kwargs[key] = delta[key]
        return result

    def _create_chat_result(self, response, generation_info=None):
        result = super()._create_chat_result(response, generation_info)
        payload = response if isinstance(response, dict) else response.model_dump()
        for generation, choice in zip(
            result.generations, payload.get("choices") or [], strict=False
        ):
            message = choice.get("message") or {}
            for key in ("reasoning_content", "reasoning"):
                if isinstance(message.get(key), str):
                    generation.message.additional_kwargs[key] = message[key]
        return result
