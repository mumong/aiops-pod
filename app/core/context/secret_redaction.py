"""Secret values never enter model context, archives or the stream.

Run ef5cbfed (runner level 2): a short ``kubectl get secret -o yaml`` result took the
raw-passthrough path, so ``data`` (base64) and the plaintext in the
``last-applied-configuration`` annotation reached the model; the key-only Secret
extractor only ran on summarised results. The same path existed on the center,
whose MCP identity has always been able to read Secrets.

Tool output is therefore redacted where it enters AIOps, before any summary,
archive or event is derived from it. Every Secret object (also inside a List)
keeps its keys; each value becomes ``<redacted: N bytes>`` and the
last-applied annotation is dropped. A Secret document that cannot be parsed is
replaced as a whole rather than passed through.
"""

from __future__ import annotations

import json
import re
from typing import Any, Tuple

LAST_APPLIED = "kubectl.kubernetes.io/last-applied-configuration"
_MAY_CONTAIN_SECRET = re.compile(r"""kind["']?\s*:\s*["']?Secret\b""")
_UNPARSEABLE = (
    "<Secret 内容已整体脱敏：输出包含 Secret 对象但无法安全解析；"
    "需要键名时请用 kubectl get secret <名称> -o yaml，系统会只保留键名>"
)


def _scrub(node: Any) -> bool:
    """Redact Secret objects inside ``node`` in place; True when anything changed."""
    changed = False
    if isinstance(node, list):
        for item in node:
            changed |= _scrub(item)
        return changed
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Secret":
        for field in ("data", "stringData"):
            values = node.get(field)
            if isinstance(values, dict):
                node[field] = {
                    key: f"<redacted: {len(str(value or ''))} bytes>"
                    for key, value in values.items()
                }
                changed = True
        annotations = (node.get("metadata") or {}).get("annotations")
        if isinstance(annotations, dict) and LAST_APPLIED in annotations:
            annotations.pop(LAST_APPLIED)
            changed = True
    for key in ("items", "objects"):
        if key in node:
            changed |= _scrub(node[key])
    return changed


def redact_secret_values(text: str) -> Tuple[str, bool]:
    """(text with Secret values redacted, whether a Secret was found)."""
    if not text or not _MAY_CONTAIN_SECRET.search(text):
        return text, False
    try:
        doc = json.loads(text)
    except ValueError:
        doc = None
    if doc is not None:
        return (
            (json.dumps(doc, ensure_ascii=False, indent=2), True) if _scrub(doc) else (text, False)
        )
    try:
        import yaml

        docs = list(yaml.safe_load_all(text))
    except Exception:  # noqa: BLE001 - unparseable output that mentions a Secret
        return _UNPARSEABLE, True
    if not any([_scrub(item) for item in docs]):  # a list: every document is scrubbed
        return text, False
    return yaml.safe_dump_all(docs, allow_unicode=True, sort_keys=False), True
