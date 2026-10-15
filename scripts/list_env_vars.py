#!/usr/bin/env python3
"""Print a Markdown table of environment variables read under app/ (os.getenv / os.environ.get).

Regenerate docs/configuration-env.md with:
    python scripts/list_env_vars.py > docs/configuration-env.md
"""

import ast
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READERS = {"os.getenv", "os.environ.get", "getenv", "environ.get"}

HEADER = """# 环境变量清单

> 由 `python scripts/list_env_vars.py > docs/configuration-env.md` 生成，请勿手工编辑。
> 优先级通常为：环境变量 > `config.yaml` > 代码默认值。另有动态变量 `WORKFLOW_MAX_STEPS_<NODE>`
> （见 `app/core/service.py` 的 `get_node_max_steps`）。Secret 类变量（如 `LLM_API_KEY`）只通过 K8s Secret 注入。

"""


def collect():
    found = collections.defaultdict(lambda: {"defaults": set(), "where": []})
    for path in sorted((ROOT / "app").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if not (
                isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant)
            ):
                continue
            if (ast.get_source_segment(source, node.func) or "") not in READERS:
                continue
            entry = found[node.args[0].value]
            entry["defaults"].add(
                ast.get_source_segment(source, node.args[1]) if len(node.args) > 1 else "—"
            )
            entry["where"].append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return found


def main():
    rows = ["| 变量 | 默认值 | 读取位置 |", "|---|---|---|"]
    for name, entry in sorted(collect().items()):
        defaults = " / ".join(sorted(d.replace("|", "\\|") for d in entry["defaults"]))
        where = ", ".join(entry["where"][:3]) + (" …" if len(entry["where"]) > 3 else "")
        rows.append(f"| `{name}` | {defaults} | {where} |")
    print(HEADER + "\n".join(rows))


if __name__ == "__main__":
    main()
