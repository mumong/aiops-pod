# 环境变量清单

> 由 `python scripts/list_env_vars.py > docs/configuration-env.md` 生成，请勿手工编辑。
> 优先级通常为：环境变量 > `config.yaml` > 代码默认值。另有动态变量 `WORKFLOW_MAX_STEPS_<NODE>`
> （见 `app/core/service.py` 的 `get_node_max_steps`）。Secret 类变量（如 `LLM_API_KEY`）只通过 K8s Secret 注入。

| 变量 | 默认值 | 读取位置 |
|---|---|---|
| `AIOPS_AUTONOMOUS_PARALLEL_WORKERS` | "3" | app/core/remediation/jobs.py:60, app/core/workflow/nodes/autonomous_parallel.py:187 |
| `AIOPS_COMPACTION_WORKERS` | "3" | app/core/aicall/working_context.py:196 |
| `AIOPS_CONTEXT_ARCHIVE_ROOT` | "" | app/core/context/archive.py:23 |
| `AIOPS_EVIDENCE_HISTORY_TOKENS` | "24000" | app/core/context/evidence_policy.py:21 |
| `AIOPS_EVIDENCE_RECENT_TOKENS` | "8000" | app/core/context/evidence_policy.py:22 |
| `AIOPS_EVIDENCE_RESULT_TOKENS` | "4096" | app/core/context/evidence_policy.py:20 |
| `AIOPS_EVIDENCE_VIEW_MODE` | "legacy" | app/core/aicall/builtin_tools.py:273, app/core/context/evidence_policy.py:15, app/core/context/observation.py:132 |
| `AIOPS_MODEL_METADATA_FILE` | "" | app/core/context/budget.py:345 |
| `AIOPS_QUERY_TOOL_TIMEOUT_SECONDS` | "60" | app/core/workflow/nodes/query_answer.py:33 |
| `AIOPS_REPAIR_RECORD_ROOT` | — | app/core/remediation/records.py:29 |
| `AIOPS_THINK_STREAM_MAX_CHARS` | — | app/core/service.py:593 |
| `AIOPS_THINK_STREAM_MODE` | — | app/core/service.py:587 |
| `AIOPS_TIKTOKEN_ENCODING` | "" | app/core/context/budget.py:99, app/core/service.py:150 |
| `AIOPS_TOKENIZER_JSON_PATH` | "" | app/core/context/budget.py:81, app/core/service.py:144 |
| `API_HOST` | "0.0.0.0" | app/main.py:164 |
| `API_PORT` | "8000" | app/main.py:163 |
| `CONFIG_FILE` | — | app/core/environment.py:67 |
| `DEEPSEEK_API_KEY` | — | app/core/service.py:341 |
| `HOLMES_INIT_TIMEOUT_SECONDS` | "0" | app/main.py:93 |
| `HOSTNAME` | "N/A" / 'localhost' | app/core/environment.py:103, app/core/environment.py:109 |
| `KUBERNETES_SERVICE_HOST` | 'N/A' / — | app/core/environment.py:32, app/core/environment.py:99 |
| `KUBERNETES_SERVICE_PORT` | 'N/A' | app/core/environment.py:100 |
| `LANGFUSE_PUBLIC_KEY` | — | app/core/aicall/client.py:2067 |
| `LANGFUSE_SECRET_KEY` | — | app/core/aicall/client.py:2067 |
| `LLM_API_BASE` | — | app/core/service.py:358 |
| `LLM_API_KEY` | — | app/core/service.py:339 |
| `LLM_MODEL` | — | app/core/service.py:351 |
| `LLM_REASONING_EFFORT` | "" | app/core/aicall/client.py:191 |
| `LOG_LEVEL` | "INFO" | app/main.py:23 |
| `MCP_AUTO_START_LOCAL` | "false" | app/main.py:60 |
| `METRICS_ENABLED` | "true" / — | app/core/workflow/metrics.py:33, app/core/workflow/metrics.py:42 |
| `METRICS_EVIDENCE_THRESHOLD` | "0.9" / — | app/core/workflow/metrics.py:32, app/core/workflow/metrics.py:49 |
| `METRICS_MTTR_THRESHOLD` | "600" / — | app/core/workflow/metrics.py:30, app/core/workflow/metrics.py:45 |
| `METRICS_RCA_CONFIDENCE_THRESHOLD` | "0.8" / — | app/core/workflow/metrics.py:31, app/core/workflow/metrics.py:47 |
| `MODEL_CONTEXT_WINDOW` | "" / "32000" / "54000" | app/core/aicall/working_context.py:118, app/core/aicall/working_context.py:155, app/core/aicall/working_context.py:341 … |
| `OPENAI_API_KEY` | — | app/core/service.py:342 |
| `POD_NAME` | os.getenv("HOSTNAME", "N/A") | app/core/environment.py:103 |
| `POD_NAMESPACE` | "N/A" | app/core/environment.py:104 |
| `REPORTS_DIR` | "/tmp/aiops/reports" | app/api/info_routes.py:18, app/core/federation/agent.py:456, app/core/federation/aggregator.py:101 … |
| `THINK_STREAM_MAX_CHARS` | — | app/core/service.py:594 |
| `THINK_STREAM_MODE` | — | app/core/service.py:588 |
| `WORKFLOW_STREAM_HEARTBEAT_SECONDS` | "15" | app/core/workflow/executor.py:402 |
