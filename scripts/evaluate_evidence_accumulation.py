#!/usr/bin/env python3
"""Synthetic serial accumulation using the real history middleware and live LLM.

No cluster tool runs or writes. The model only compresses frozen synthetic facts.
This tests history replacement and evidence retention, not autonomous diagnosis.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages

from app.core.aicall.client import AICall, _parse_model
from app.core.aicall.working_context import WorkingContextMiddleware
from app.core.context.budget import count_tokens
from app.core.context.observation import ObservationProcessor
from scripts.evaluate_evidence_view import model_config


async def evaluate(output):
    output.mkdir(parents=True, exist_ok=False)
    os.environ["AIOPS_EVIDENCE_VIEW_MODE"] = "compact"
    os.environ["AIOPS_CONTEXT_ARCHIVE_ROOT"] = str(output / "archives")
    os.environ["MODEL_CONTEXT_WINDOW"] = "54000"
    config = model_config()
    name, base = _parse_model(config["LLM_MODEL"], config["LLM_API_BASE"])
    model = ChatOpenAI(model=name, base_url=base, api_key=config["LLM_API_KEY"],
                       reasoning_effort=config.get("LLM_REASONING_EFFORT", "low"),
                       timeout=90, max_retries=0, max_tokens=3000)
    client = AICall(model=config["LLM_MODEL"], api_base=base, api_key=config["LLM_API_KEY"])
    client.query_context_state_compaction = True
    question = "冻结合成实验：最终请核对每批记录最后一个实体的 value、units、observed_at；不要推断线上状态。"
    events, steps = [], []
    middleware = WorkingContextMiddleware(client, model, model, [], "仅依据证据回答。", question,
                                          "serial-live-summary", "query_collect", lambda **e: events.append(e))
    processor = ObservationProcessor()
    state = [HumanMessage(content=question)]
    start = time.monotonic()
    for index in range(18):
        # Deliberately below the per-result cap, but above the aggregate cap
        # after several serial interactions; distinct values prevent dedup.
        records = [{"entity": f"batch-{index}-item-{j}", "value": index * 1000 + j,
                    "units": "bytes", "observed_at": f"synthetic-t{index}-{j}",
                    "detail": f"frozen independent measurement {index}-{j} " * 4}
                   for j in range(34)]
        raw = json.dumps({"origin": "synthetic_not_live", "records": records}, ensure_ascii=False)
        obs = processor.process("serial-live-summary", "query_collect", index + 1, "future_measurement_tool", raw)
        state = add_messages(state, [AIMessage(content="", tool_calls=[{
            "name": "future_measurement_tool", "args": {"batch": index}, "id": f"batch-{index}"}]),
            ToolMessage(content=obs["summary"], tool_call_id=f"batch-{index}",
                        additional_kwargs={"aiops_raw_ref": obs["raw_ref"], "aiops_semantic_success": True})])
        before = middleware.tool_history_tokens(state)
        update = await middleware.abefore_model({"messages": state}, None)
        if update:
            state = add_messages(state, update["messages"])
        row = {"index": index, "before": before, "after": middleware.tool_history_tokens(state),
               "compacted": bool(update), "view_tokens": count_tokens(obs["summary"])["tokens"]}
        steps.append(row)
        print(json.dumps(row), flush=True)
    result = {"model": config["LLM_MODEL"], "origin": "synthetic_serial_replay_live_compactor",
              "seconds": time.monotonic() - start, "steps": steps,
              "events": events, "final_messages": [m.model_dump() for m in state]}
    (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    compact_at = [r["index"] for r in steps if r["compacted"]]
    assert compact_at, "Replay did not exercise actual compaction"
    assert all(b - a >= 3 for a, b in zip(compact_at, compact_at[1:], strict=False)), "Repeated compaction without headroom"
    assert all(r["after"] <= 24000 for r in steps), "Cumulative limit exceeded after replacement"
    print(json.dumps({"compacted_at": compact_at, "seconds": result["seconds"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(evaluate(parser.parse_args().output))
