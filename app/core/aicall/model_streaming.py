"""Preserve optional provider-visible reasoning without changing requests."""

from langchain_openai import ChatOpenAI


class VisibleChatOpenAI(ChatOpenAI):
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
