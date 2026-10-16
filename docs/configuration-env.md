# 环境变量清单

> 由 `python scripts/list_env_vars.py > docs/configuration-env.md` 生成，请勿手工编辑。
> 优先级通常为：环境变量 > `config.yaml` > 代码默认值。另有动态变量 `WORKFLOW_MAX_STEPS_<NODE>`
> （见 `app/core/service.py` 的 `get_node_max_steps`）。Secret 类变量（如 `LLM_API_KEY`）只通过 K8s Secret 注入。

| 变量 | 默认值 | 读取位置 |
|---|---|---|
| `AICALL_COMPACTION_MAX_OUTPUT_TOKENS` | 3000 | app/core/aicall/output_budget.py:21 |
| `AICALL_DELIVERY_MAX_OUTPUT_TOKENS` | 10000 | app/core/aicall/output_budget.py:20 |
| `AICALL_DELIVERY_RETRY_MULTIPLIER` | 2 | app/core/aicall/output_budget.py:23 |
| `AICALL_MAX_IDENTICAL_CALLS` | 3 | app/core/aicall/guards.py:12 |
| `AICALL_MAX_OUTPUT_TOKENS` | 6000 | app/core/aicall/output_budget.py:19 |
| `AICALL_MAX_TOOL_CALLS_PER_TURN` | 16 | app/core/aicall/guards.py:11 |
| `AICALL_MODEL_IDLE_TIMEOUT_SECONDS` | _DEFAULT_MODEL_IDLE_TIMEOUT_SECONDS | app/core/aicall/client.py:202 |
| `AICALL_RECENT_KEEP_RATIO` | 0.15 | app/core/context/window_policy.py:18 |
| `AICALL_RECENT_KEEP_TOKENS` | 8000 | app/core/context/window_policy.py:17 |
| `AICALL_REPEAT_PAGE_CHARS` | 3000 | app/core/aicall/guards.py:13 |
| `AICALL_ROUTER_MAX_OUTPUT_TOKENS` | 1200 | app/core/aicall/output_budget.py:22 |
| `AICALL_STRUCTURED_CALL_TIMEOUT_SECONDS` | _DEFAULT_STRUCTURED_CALL_TIMEOUT_SECONDS | app/core/aicall/client.py:170 |
| `AIOPS_AUTONOMOUS_PARALLEL_WORKERS` | "3" / self.DEFAULT_LANE_WORKERS | app/core/remediation/jobs.py:88, app/core/workflow/nodes/autonomous_parallel.py:135 |
| `AIOPS_COMPACTION_WORKERS` | "3" | app/core/aicall/working_context.py:306 |
| `AIOPS_CONTEXT_ARCHIVE_ROOT` | "" | app/core/context/archive.py:22 |
| `AIOPS_EVIDENCE_HISTORY_TOKENS` | "24000" | app/core/context/evidence_policy.py:22 |
| `AIOPS_EVIDENCE_RECENT_TOKENS` | "8000" | app/core/context/evidence_policy.py:23 |
| `AIOPS_EVIDENCE_RESULT_TOKENS` | "4096" | app/core/context/evidence_policy.py:21 |
| `AIOPS_EVIDENCE_VIEW_MODE` | "legacy" | app/core/aicall/builtin_tools.py:329, app/core/context/evidence_policy.py:16, app/core/context/observation.py:171 |
| `AIOPS_LOG_FORMAT` | "text" | app/core/log_context.py:70 |
| `AIOPS_MODEL_METADATA_FILE` | "" | app/core/context/budget.py:340 |
| `AIOPS_QUERY_TOOL_TIMEOUT_SECONDS` | "60" | app/core/workflow/nodes/query_answer.py:33 |
| `AIOPS_REPAIR_RECORD_ROOT` | — | app/core/remediation/records.py:32 |
| `AIOPS_THINK_STREAM_MAX_CHARS` | — | app/core/service.py:652 |
| `AIOPS_THINK_STREAM_MODE` | — | app/core/service.py:646 |
| `AIOPS_TIKTOKEN_ENCODING` | "" | app/core/context/budget.py:98, app/core/service.py:160 |
| `AIOPS_TOKENIZER_JSON_PATH` | "" | app/core/context/budget.py:78, app/core/service.py:154 |
| `API_HOST` | "0.0.0.0" | app/main.py:184 |
| `API_PORT` | "8000" | app/main.py:183 |
| `CONFIG_FILE` | — | app/core/environment.py:67 |
| `DEEPSEEK_API_KEY` | — | app/core/service.py:358 |
| `HOLMES_INIT_TIMEOUT_SECONDS` | "0" | app/main.py:113 |
| `HOSTNAME` | "N/A" / "localhost" | app/core/environment.py:103, app/core/environment.py:109 |
| `KUBERNETES_SERVICE_HOST` | "N/A" / — | app/core/environment.py:32, app/core/environment.py:99 |
| `KUBERNETES_SERVICE_PORT` | "N/A" | app/core/environment.py:100 |
| `LANGFUSE_PUBLIC_KEY` | — | app/core/aicall/client.py:2638 |
| `LANGFUSE_SECRET_KEY` | — | app/core/aicall/client.py:2638 |
| `LLM_API_BASE` | — | app/core/service.py:375 |
| `LLM_API_KEY` | — | app/core/service.py:356 |
| `LLM_MODEL` | "" / — | app/core/service.py:368, app/core/workflow/case_report.py:100 |
| `LLM_REASONING_EFFORT` | "" | app/core/aicall/client.py:312 |
| `LOG_LEVEL` | "INFO" | app/main.py:24 |
| `MCP_AUTO_START_LOCAL` | "false" | app/main.py:71 |
| `METRICS_ENABLED` | "true" / — | app/core/workflow/metrics.py:33, app/core/workflow/metrics.py:46 |
| `METRICS_EVIDENCE_THRESHOLD` | "0.9" / — | app/core/workflow/metrics.py:32, app/core/workflow/metrics.py:53 |
| `METRICS_MTTR_THRESHOLD` | "600" / — | app/core/workflow/metrics.py:30, app/core/workflow/metrics.py:49 |
| `METRICS_RCA_CONFIDENCE_THRESHOLD` | "0.8" / — | app/core/workflow/metrics.py:31, app/core/workflow/metrics.py:51 |
| `MODEL_CONTEXT_WINDOW` | "" / "32000" | app/core/aicall/working_context.py:154, app/core/aicall/working_context.py:251, app/core/aicall/working_context.py:540 … |
| `OPENAI_API_KEY` | — | app/core/service.py:359 |
| `POD_NAME` | os.getenv("HOSTNAME", "N/A") | app/core/environment.py:103 |
| `POD_NAMESPACE` | "N/A" | app/core/environment.py:104 |
| `REPORTS_DIR` | "/tmp/aiops/reports" | app/api/info_routes.py:20, app/core/federation/agent.py:485, app/core/federation/aggregator.py:102 … |
| `THINK_STREAM_MAX_CHARS` | — | app/core/service.py:653 |
| `THINK_STREAM_MODE` | — | app/core/service.py:647 |
| `WORKFLOW_STREAM_HEARTBEAT_SECONDS` | "15" | app/core/workflow/executor.py:435 |
