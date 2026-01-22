#!/usr/bin/env python3
"""
导出 HolmesGPT(holmes) 内置 toolsets 的工具定义 + 相关源码文件内容到 Markdown。

目标：
- 以 deploy/configmap/config.yaml 为输入（ConfigMap 里嵌套的 data.config.yaml）
- 只导出其中 toolsets.*.enabled == true 的内置 toolsets
- 输出每个 tool 的 name/description/inputSchema（尽力抽取）
- 同时输出 toolset / tool 实现所在的源码文件路径 + 文件内容（仅限 holmes 包内文件）

注意：
- 该脚本不会修改你的业务代码；只是在本地解析配置并读取已安装 holmes 包的源码。
- 不依赖真实 LLM API Key：默认使用 DUMMY，只用于 Config 初始化（不发起推理）。
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import yaml


@dataclass(frozen=True)
class ToolExport:
    name: str
    description: str
    input_schema: Optional[Dict[str, Any]]
    tool_class: str
    tool_module: str


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_inner_holmes_config_from_configmap_yaml(configmap_yaml_path: Path) -> Tuple[Dict[str, Any], str]:
    """
    读取 deploy/configmap/config.yaml 这种 ConfigMap 格式：
      data:
        config.yaml: |
          toolsets: ...
          mcp_servers: ...
    返回：(inner_dict, inner_text)
    """
    outer = _read_yaml(configmap_yaml_path)
    data = outer.get("data") or {}
    inner_text = data.get("config.yaml")
    if isinstance(inner_text, str) and inner_text.strip():
        return yaml.safe_load(inner_text) or {}, inner_text

    # 兼容：直接就是 holmes config.yaml（非 ConfigMap 包装）
    raw = configmap_yaml_path.read_text(encoding="utf-8")
    return yaml.safe_load(raw) or {}, raw


def enabled_toolset_names(inner_cfg: Dict[str, Any]) -> List[str]:
    toolsets = inner_cfg.get("toolsets") or {}
    enabled: List[str] = []
    if isinstance(toolsets, dict):
        for name, cfg in toolsets.items():
            if isinstance(cfg, dict) and cfg.get("enabled") is True:
                enabled.append(str(name))
    return enabled


def _safe_json(obj: Any) -> str:
    """
    将对象尽量转为 JSON 可序列化结构后再 dumps。
    一些 schema 里会混入自定义对象（例如 ToolParameter），这里做容错处理。
    """

    def normalize(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (str, int, float, bool)):
            return v
        if isinstance(v, bytes):
            try:
                return v.decode("utf-8", errors="replace")
            except Exception:
                return str(v)
        if isinstance(v, (list, tuple, set)):
            return [normalize(x) for x in list(v)]
        if isinstance(v, dict):
            out: Dict[str, Any] = {}
            for k, vv in v.items():
                out[str(k)] = normalize(vv)
            return out

        # pydantic v2
        if hasattr(v, "model_dump"):
            try:
                return normalize(v.model_dump())
            except Exception:
                pass
        # pydantic v1
        if hasattr(v, "dict"):
            try:
                return normalize(v.dict())
            except Exception:
                pass

        # fallback：字符串化
        return str(v)

    return json.dumps(normalize(obj), ensure_ascii=False, indent=2, sort_keys=False)


def _extract_tool_schema(tool: Any) -> Optional[Dict[str, Any]]:
    """
    尽力从不同 Tool 类型里抽取输入 schema。
    兼容 pydantic v1/v2 + 其他结构。
    """
    # 1) pydantic args_schema（常见：LangChain BaseTool）
    args_schema = getattr(tool, "args_schema", None)
    if args_schema is not None:
        try:
            # pydantic v2
            if hasattr(args_schema, "model_json_schema"):
                return args_schema.model_json_schema()
            # pydantic v1
            if hasattr(args_schema, "schema"):
                return args_schema.schema()
        except Exception:
            pass

    # 2) inputSchema / input_schema（有些工具直接挂 schema）
    for attr in ("inputSchema", "input_schema", "schema", "json_schema"):
        val = getattr(tool, attr, None)
        if isinstance(val, dict):
            return val

    # 3) parameters (OpenAI style)
    params = getattr(tool, "parameters", None)
    if isinstance(params, dict):
        return params

    return None


def _tool_description(tool: Any) -> str:
    for attr in ("description", "desc", "help", "tool_description"):
        val = getattr(tool, attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _tool_name(tool: Any) -> str:
    val = getattr(tool, "name", None)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return tool.__class__.__name__


def _iter_related_source_files(
    *,
    toolset: Any,
    tools: Iterable[Any],
    holmes_pkg_dir: Path,
) -> List[Path]:
    """
    收集和该 toolset/tools “强相关”的源码文件：
    - toolset class 定义文件
    - tool class 定义文件
    - tool.func / tool._run / tool._arun（如果能定位到源文件）

    只返回 holmes 包目录下的文件，避免把第三方库源码也全打出来。
    """
    files: Set[Path] = set()

    def add_file(fp: Optional[str]) -> None:
        if not fp:
            return
        p = Path(fp).resolve()
        try:
            p.relative_to(holmes_pkg_dir)
        except Exception:
            return
        if p.exists() and p.is_file():
            files.add(p)

    add_file(inspect.getsourcefile(toolset.__class__))

    for t in tools:
        add_file(inspect.getsourcefile(t.__class__))
        for attr in ("func", "_run", "_arun", "run"):
            fn = getattr(t, attr, None)
            if fn is None:
                continue
            try:
                add_file(inspect.getsourcefile(fn))
            except Exception:
                continue

    return sorted(files, key=lambda p: str(p))


def _read_text_file(path: Path, *, max_bytes: int) -> str:
    data = path.read_bytes()
    truncated = False
    if len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    text = data.decode("utf-8", errors="replace")
    if truncated:
        text += "\n\n# --- TRUNCATED: file exceeded max_bytes ---\n"
    return text


def export_markdown(
    *,
    out_path: Path,
    configmap_yaml_path: Path,
    api_key: str,
    model: str,
    max_steps: int,
    max_bytes_per_file: int,
) -> None:
    inner_cfg, inner_text = load_inner_holmes_config_from_configmap_yaml(configmap_yaml_path)
    enabled_names = enabled_toolset_names(inner_cfg)

    import holmes  # noqa: WPS433
    from holmes.config import Config  # noqa: WPS433

    holmes_pkg_dir = Path(holmes.__file__).resolve().parent

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml.safe_dump(inner_cfg, allow_unicode=True, sort_keys=False))
        tmp_cfg_path = Path(f.name)

    try:
        cfg = Config.load_from_file(
            config_file=tmp_cfg_path,
            api_key=api_key,
            model=model,
            max_steps=max_steps,
        )
        ai = cfg.create_console_toolcalling_llm()
        tool_executor = ai.tool_executor

        # toolset objects by name
        toolsets_by_name: Dict[str, Any] = {}
        for ts in tool_executor.toolsets:
            ts_name = getattr(ts, "name", ts.__class__.__name__)
            toolsets_by_name[str(ts_name)] = ts

        lines: List[str] = []
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"# Holmes 内置工具导出\n")
        lines.append(f"- 生成时间: **{now}**\n")
        lines.append(f"- Python: `{sys.version.split()[0]}`\n")
        lines.append(f"- holmes 版本: `{getattr(holmes, '__version__', '?')}`\n")
        lines.append(f"- holmes 包路径: `{holmes_pkg_dir}`\n")
        lines.append(f"- 输入配置: `{configmap_yaml_path}`\n")
        lines.append("\n---\n")

        lines.append("## 本次导出的 toolsets（按 config.yaml 中 enabled=true）\n")
        if enabled_names:
            for n in enabled_names:
                lines.append(f"- `{n}`\n")
        else:
            lines.append("- （未发现 enabled=true 的 toolsets；请检查你的 `deploy/configmap/config.yaml`）\n")

        lines.append("\n---\n")
        lines.append("## 原始 inner config.yaml（来自 ConfigMap.data['config.yaml']）\n")
        lines.append("```yaml\n")
        lines.append(inner_text.rstrip() + "\n")
        lines.append("```\n")

        # 导出每个 toolset
        for ts_name in enabled_names:
            ts = toolsets_by_name.get(ts_name)
            lines.append("\n---\n")
            lines.append(f"## Toolset: `{ts_name}`\n")
            if ts is None:
                lines.append("- **状态**: 未在运行时 tool_executor.toolsets 中找到（可能未安装依赖或加载失败）\n")
                continue

            ts_class = ts.__class__.__name__
            ts_module = getattr(ts.__class__, "__module__", "?")
            ts_enabled = getattr(ts, "enabled", None)
            ts_status = getattr(getattr(ts, "status", None), "value", getattr(ts, "status", None))
            ts_error = getattr(ts, "error", None)

            lines.append(f"- **类**: `{ts_class}`\n")
            lines.append(f"- **模块**: `{ts_module}`\n")
            lines.append(f"- **enabled**: `{ts_enabled}`\n")
            lines.append(f"- **status**: `{ts_status}`\n")
            if ts_error:
                lines.append(f"- **error**: `{str(ts_error)[:400]}`\n")

            raw_tools = getattr(ts, "tools", None) or []
            registered_tools = []
            for t in raw_tools:
                tname = _tool_name(t)
                if tname in tool_executor.tools_by_name:
                    registered_tools.append(t)

            exports: List[ToolExport] = []
            for t in registered_tools:
                exports.append(
                    ToolExport(
                        name=_tool_name(t),
                        description=_tool_description(t),
                        input_schema=_extract_tool_schema(t),
                        tool_class=t.__class__.__name__,
                        tool_module=getattr(t.__class__, "__module__", "?"),
                    )
                )

            lines.append(f"\n### 已注册工具（{len(exports)} 个）\n")
            if not exports:
                lines.append("- （此 toolset 未注册任何工具，或加载失败）\n")
            else:
                lines.append("| tool | description | class | module |\n")
                lines.append("|---|---|---|---|\n")
                for te in exports:
                    desc = te.description.replace("\n", " ").strip()
                    if len(desc) > 160:
                        desc = desc[:160] + "…"
                    lines.append(f"| `{te.name}` | {desc} | `{te.tool_class}` | `{te.tool_module}` |\n")

                lines.append("\n### 工具输入参数（Schema）\n")
                for te in exports:
                    lines.append(f"\n#### `{te.name}`\n")
                    if te.input_schema is None:
                        lines.append("- （未能从对象上抽取 schema；可能是无参工具或 schema 定义方式不同）\n")
                    else:
                        lines.append("```json\n")
                        lines.append(_safe_json(te.input_schema) + "\n")
                        lines.append("```\n")

            # 源码文件
            files = _iter_related_source_files(toolset=ts, tools=registered_tools, holmes_pkg_dir=holmes_pkg_dir)
            lines.append(f"\n### 相关源码文件（holmes 包内，{len(files)} 个）\n")
            for fp in files:
                rel = fp.relative_to(holmes_pkg_dir)
                lines.append(f"\n#### `{rel}`\n")
                lines.append(f"- 绝对路径: `{fp}`\n")
                lines.append("```python\n")
                lines.append(_read_text_file(fp, max_bytes=max_bytes_per_file).rstrip() + "\n")
                lines.append("```\n")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(lines), encoding="utf-8")
    finally:
        try:
            tmp_cfg_path.unlink()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Export holmes builtin toolsets into a Markdown dump.")
    parser.add_argument(
        "--configmap",
        default="/root/huhu/agent/robusta/deploy/configmap/config.yaml",
        help="ConfigMap YAML path (contains data.config.yaml) or direct holmes config.yaml",
    )
    parser.add_argument(
        "--out",
        default="/root/huhu/agent/robusta/test/holmes_builtin_tools_dump.md",
        help="Output markdown path",
    )
    parser.add_argument("--api-key", default=os.getenv("DEEPSEEK_API_KEY", "DUMMY"))
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat"))
    parser.add_argument("--max-steps", type=int, default=1)
    parser.add_argument("--max-bytes-per-file", type=int, default=250_000)
    args = parser.parse_args()

    export_markdown(
        out_path=Path(args.out),
        configmap_yaml_path=Path(args.configmap),
        api_key=args.api_key,
        model=args.model,
        max_steps=args.max_steps,
        max_bytes_per_file=args.max_bytes_per_file,
    )

    print(f"OK: wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

