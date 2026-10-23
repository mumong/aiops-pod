#!/usr/bin/env python3
"""Call the AIOps A2A server with the official a2a-sdk 0.3 client."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

import httpx
from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.types import Message, Task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Kubernetes diagnosis or query question")
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--token", default="", help="Optional A2A bearer token")
    parser.add_argument(
        "--mode",
        choices=("diagnosis", "query"),
        default="diagnosis",
        help="query selects the existing /query fast path",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Use message/send instead of message/stream",
    )
    return parser


def _print_artifacts(task: Task) -> None:
    for artifact in task.artifacts or []:
        print(f"\n--- {artifact.name or artifact.artifact_id} ---")
        for part in artifact.parts:
            root: Any = part.root
            if getattr(root, "kind", None) == "text":
                print(root.text)
            elif getattr(root, "kind", None) == "data":
                print(root.data)


async def run(args: argparse.Namespace) -> None:
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    async with httpx.AsyncClient(headers=headers, timeout=None) as http_client:
        client = await ClientFactory.connect(
            args.url,
            client_config=ClientConfig(
                streaming=not args.no_stream,
                httpx_client=http_client,
                accepted_output_modes=["text/markdown"],
            ),
        )
        message = create_text_message_object(content=args.question)
        final_task: Task | None = None
        async for result in client.send_message(
            message,
            request_metadata={"aiops_mode": args.mode},
        ):
            if isinstance(result, Message):
                print(result.model_dump_json(indent=2))
                continue
            task, update = result
            final_task = task
            update_kind = getattr(update, "kind", "task") if update else "task"
            print(f"[{task.status.state}] {update_kind}")

        if final_task is not None:
            _print_artifacts(final_task)


def main() -> None:
    asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    main()
