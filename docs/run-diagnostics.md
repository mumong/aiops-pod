# 运行诊断：账本、工程异常分类与运行报告

[返回 README](../README.md)。本文说明"一次运行结束后，怎样在一分钟内看懂它发生了什么"。这里诊断的是 **Agent 运行本身**（时间花在哪、哪些护栏触发、模型/工具/服务谁出了问题），不是 Kubernetes 故障的根因——后者由诊断报告回答。

## 数据来源（无新埋点）

每次模型调用本来就会产生事件流：`ai_usage`（每轮输入/输出 token、模型耗时）、`tool_start/tool_result`、`execution_incomplete`、`context_compacted`、`structured_finalization`、`tool_call_args_repaired`；工具消息上带护栏标记（`aiops_repeat_notice / aiops_repeat_page / aiops_turn_cap / aiops_tool_error`）。账本只是把这些事实收拢成一个文件。

## 产物（都在归档目录 `<AIOPS_CONTEXT_ARCHIVE_ROOT>/<run_id>/`）

| 文件 | 内容 | 产生时机 |
|---|---|---|
| `tools/NNN-<node>-<tool>.call.json` | 工具调用参数、call_id、护栏标记 | 每次工具结果落盘时（与 `.raw.txt` 同名） |
| `ledger/<node>.json` | 本次模型调用账本：每轮 token/耗时/发起的工具数、每个工具调用的状态与护栏、计数、结束原因 | `AICall.call()` 结束（lane 写在 `<run_id>-gN/ledger/`） |
| `run_report.json` / `run_report.md` | 运行报告：路由/范围/结果、节点耗时、定位目标、lane 结果、每个调用的账本摘要、**工程异常发现** | 工作流结束（`executor._finish_run`） |

日志里对应两类行，可直接 grep：

```text
[run_summary] run=… route=… outcome=… elapsed=…s calls=… rounds=… tools=… repeats=… capped=… findings=…
[run_finding] run=… code=… where=… <evidence>          # 仅 warning/error 级别
```

`AIOPS_LOG_FORMAT=json` 时所有日志按 JSON 行输出（含 run/node/lane 字段），便于日志系统聚合。

## 工程异常类型（`app/core/diagnostics/findings.py`）

阈值来自运行时同一套护栏/预算（`llm.agent_guards`、`llm.output_tokens`），因此"有发现"≈"某个护栏触发或逼近"。

| code | 级别 | 含义 | 先看什么 |
|---|---|---|---|
| `tool_call_burst` | warning | 单条模型消息发起的工具调用数超过每轮上限 | 模型退化重复；上限已拦截执行，但生成时间仍被消耗 |
| `identical_call_repeats` | info | 同一调用被重复（提示/分页应答） | `tools[].guard` |
| `repeat_limit_stop` | warning | 重复达到上限，阶段确定性停止 | 已基于现有材料交付 |
| `malformed_tool_args_repaired` | warning | 流式工具参数拼接损坏，发送前已修复 | 模型/解析层；原本会导致 HTTP 400 |
| `step_limit` / `agent_timeout` | warning / error | 步数或时限到顶 | 轮次为何无产出 |
| `provider_error` | error | 模型服务请求失败 | 网关 / vLLM 该时段日志 |
| `model_stalled` | error | 流 180s 无字节 | 模型服务 |
| `structured_finalization` / `empty_structured_delivery` | info / error | 收卷成功 / 重试后仍无结构化结果 | `cases/invalid-output.txt` |
| `tool_failures` | info | 工具返回错误 | 工具契约或参数 |
| `large_tool_output_bounded` | info | 大结果被有界展示（原文已归档） | `raw_ref` 回读 |
| `context_compacted` | info | 发生过上下文压缩 | `compactions/` |
| `long_model_round` / `output_budget_exhausted_round` | warning | 单轮 ≥60s / 输出打满预留 | 推理过长或 token 空转 |

## 读取方式

- API：`GET /runs/{run_id}`（JSON）、`GET /runs/{run_id}/report.md`（Markdown）——前端与 A2A 同一入口。
- 脚本：`scripts/run_report.py <run_id>`（Pod 内 `kubectl exec … python - <run_id> < scripts/run_report.py`）。
- 归档：直接看 `run_report.md`。

## 设计边界

- 账本和发现是 **派生数据**，写入失败只记日志，不影响运行。
- 分类规则只描述 Agent 行为，不含任何 Kubernetes 故障语义；新 Pod、新异常类型不需要改这里。
- 新增护栏时：在工具消息上加 `aiops_*` 标记或记录一个事件，再在 `findings.py` 加一条规则。

模型本身、推理服务（vLLM/网关）与采样配置引起的异常分类、出处和对照实验见 [LLM 自身异常排查手册](llm-model-anomalies.md)。
