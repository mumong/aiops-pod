"""Optional gzip+base64 encoding of command output on the tunnel.

xnet buffers each response and base64-encodes it inside a JSON frame, so large
JSON listings travel much smaller compressed (contracts/runner-api.md).
"""

from __future__ import annotations

import base64
import gzip
from typing import Any, Dict, Tuple

ENCODING = "gzip+base64"


def _pack(text: str) -> str:
    return base64.b64encode(gzip.compress(text.encode("utf-8"), compresslevel=6)).decode("ascii")


def _unpack(blob: str) -> str:
    return gzip.decompress(base64.b64decode(blob or "")).decode("utf-8", "replace") if blob else ""


def encode_streams(result: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in result.items() if k not in ("stdout", "stderr")}
    out.update(
        encoding=ENCODING,
        stdout_b64=_pack(result.get("stdout") or ""),
        stderr_b64=_pack(result.get("stderr") or ""),
    )
    return out


def decode_streams(result: Dict[str, Any]) -> Tuple[str, str]:
    if result.get("encoding") == ENCODING:
        return _unpack(result.get("stdout_b64", "")), _unpack(result.get("stderr_b64", ""))
    return result.get("stdout") or "", result.get("stderr") or ""
