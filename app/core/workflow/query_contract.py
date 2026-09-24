"""Query response contract and narrow JSON recovery, independent of graph nodes."""

import json
import re

from pydantic import BaseModel, Field


class QueryAnswer(BaseModel):
    intent: str = Field(description="本次理解的用户目标，不是固定故障分类")
    scope: str = Field(description="实际回答的对象与时间范围；未知时明确说明")
    status: str = Field(description="answered / partial / clarify / unavailable")
    answer: str = Field(
        description="可直接展示的完整中文 Markdown 回答，包括必要事实、解释、限制或澄清"
    )
    evidence_refs: list[str] = Field(
        default_factory=list, description="实际工具返回中的来源引用，不编造"
    )
    runbooks: list[str] = Field(
        default_factory=list, description="本次实际读取的手册，不是所有可用手册"
    )
    missing: list[str] = Field(default_factory=list, description="未回答的项目和原因")


def parse_query_answer(raw):
    """Validate JSON; narrowly recover unescaped quotes/newlines inside answer only."""
    from app.core.aicall.client import AICall

    parsed = AICall.extract_json_payload(raw)
    try:
        return QueryAnswer.model_validate(parsed).model_dump(), False
    except (ValueError, TypeError):
        pass
    text = raw.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    start = re.search(r'"answer"\s*:\s*"', text)
    if not start or not text.startswith("{"):
        return None, False
    candidates = []
    for end in re.finditer(
        r'"\s*,\s*"(?:evidence_refs|runbooks|missing)"\s*:', text[start.end() :]
    ):
        stop = start.end() + end.start()
        body = text[start.end() : stop]
        escaped, index = [], 0
        while index < len(body):
            char = body[index]
            if char == "\\" and index + 1 < len(body):
                escaped.append(body[index : index + 2])
                index += 2
                continue
            escaped.append(json.dumps(char, ensure_ascii=False)[1:-1])
            index += 1
        try:
            # Prefix and suffix must already be valid; never infer missing fields.
            value = json.loads(text[: start.end()] + "".join(escaped) + text[stop:])
            candidates.append(QueryAnswer.model_validate(value).model_dump())
        except (ValueError, TypeError):
            continue
    return (candidates[0], True) if len(candidates) == 1 else (None, False)
