"""Network smoke-test backend implementing the AIOps SSE contract."""

import json
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "healthy"}


async def _run(request: Request, mode: str):
    form = parse_qs((await request.body()).decode())
    question = (form.get("q") or [""])[0]
    answer = f"# A2A smoke report\n\nmode={mode}\n\nquestion={question}"

    async def records():
        events = [
            ("run_start", {"run_id": f"smoke-{mode}"}),
            ("node_start", {"node": "conclusion"}),
            ("final", {"answer": answer}),
            ("run_end", {}),
        ]
        for event, payload in events:
            yield f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(records(), media_type="text/event-stream")


@app.post("/ask")
async def ask(request: Request):
    return await _run(request, "diagnosis")


@app.post("/query")
async def query(request: Request):
    return await _run(request, "query")
