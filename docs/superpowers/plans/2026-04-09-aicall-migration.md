# aicall 模块迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace HolmesGPT AI calling layer with self-owned `aicall` module (LangChain/LangGraph), achieving full prompt control.

**Architecture:** `app/core/aicall/` provides `AICall.call()` (ReAct loop) and `call_simple()` (direct LLM). MCP tools adapted via `MCPToolAdapter`. Service.py split into config + service. Holmes/ directory deleted.

**Tech Stack:** LangChain (ChatOpenAI), LangGraph, litellm, MCP SSE

**Spec:** `docs/superpowers/specs/2026-04-09-aicall-migration-design.md`

**子计划文件:**
- [Phase 1: aicall 模块](./phase1-aicall-module.md)
- [Phase 2: 节点迁移](./phase2-node-migration.md)
- [Phase 3: service 拆分 + holmes 清理](./phase3-service-split.md)
- [Phase 4: 代码精简](./phase4-code-cleanup.md)

---

## 文件结构总览

### 新建文件
| 文件 | 职责 | 行数估算 |
|------|------|----------|
| `app/core/aicall/__init__.py` | 导出 AICall, AICallResult | ~10 |
| `app/core/aicall/types.py` | AICallResult, ThinkingEvent 类型 | ~60 |
| `app/core/aicall/client.py` | AICall 核心类（ReAct loop） | ~200 |
| `app/core/aicall/streaming.py` | 流式事件处理 | ~80 |
| `app/core/aicall/tools.py` | MCP → LangChain Tool 适配器 | ~120 |
| `app/core/config/__init__.py` | 导出 | ~5 |
| `app/core/config/loader.py` | YAML + 环境变量加载 | ~150 |
| `app/core/config/settings.py` | AppConfig 数据类 | ~60 |
| `app/core/runbook/catalog.py` | RunbookCatalog（替代 holmes） | ~80 |
| `app/core/workflow/reporter.py` | 报告保存 + 指标提取 | ~200 |
| `mcpstander/.../investigation.py` | TodoWrite + fetch_runbook MCP | ~100 |

### 修改文件
| 文件 | 改动 |
|------|------|
| `app/core/workflow/nodes/base.py` | `_call_llm()` → 调用 AICall |
| `app/core/workflow/executor.py` | 拆出 reporter，精简到 ~400 行 |
| `app/core/service.py` | 精简到 ~200 行 |
| `requirements.txt` | 移除 holmesgpt，确认 langchain |

### 删除文件
| 文件 | 替代 |
|------|------|
| `app/core/holmes/call_wrapper.py` | → aicall/client.py |
| `app/core/holmes/config_loader.py` | → config/loader.py |
| `app/core/holmes/query_stream.py` | → service.py |
| `app/core/holmes/streaming.py` | → aicall/streaming.py |
| `app/core/holmes/introspection.py` | → config/loader.py |
| `app/core/holmes/event_mapper.py` | → aicall/types.py |
| `app/core/holmes/tool_logging_patch.py` | → aicall 内置 |
