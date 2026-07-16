# Generic CrashLoopBackOff Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建并真实验证一个非 OOM 的常见 CrashLoopBackOff 场景，证明现有 AIOps MCP 和 Robusta 能按 Pod 通用采集并构建 metrics、logs、traces、topology 因果证据。

**Architecture:** 在 Robusta 仓库新增独立测试环境。Driver 通过 Service 调用缺少必需配置的业务 API；API 返回 500、记录 trace 日志、导出 Tempo span，并以 exit 78 退出。生产采集器仍只接收 namespace 和 pod，不增加故障类型分支。

**Tech Stack:** Kubernetes YAML、Bash、Python 标准库、OTLP HTTP/JSON、DeepFlow、Prometheus、Tempo、pytest、Robusta `/ask`。

---

### Task 1: 测试环境契约

**Files:**
- Create: `tests/unit/test_aiops_traced_config_testcase.py`
- Create: `testcases/aiops-traced-config-crashloop.yaml`
- Create: `scripts/aiops-traced-config-crashloop.sh`

- [ ] **Step 1: 先写静态契约测试**

测试 YAML 包含 Namespace、ConfigMap、Service、API Deployment 和 Driver Deployment；
业务代码必须输出 trace 字段、导出 OTLP span、返回 500 并以 78 退出。脚本必须提供
`apply|status|logs|verify|cleanup`。

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
.venv/bin/pytest -q tests/unit/test_aiops_traced_config_testcase.py
```

Expected: FAIL，原因是 YAML 或脚本尚不存在。

- [ ] **Step 3: 实现最小测试环境**

创建 `aiops-traced-config` 命名空间。API 每轮处理三次 `/checkout` 请求后退出；
Driver 持续发送带 W3C `traceparent` 的请求。

- [ ] **Step 4: 运行静态契约测试**

Run:

```bash
.venv/bin/pytest -q tests/unit/test_aiops_traced_config_testcase.py
```

Expected: PASS。

### Task 2: 真实集群验证

**Files:**
- Create: `docs/aiops-traced-config-crashloop-test-environment.md`

- [ ] **Step 1: 部署并等待异常**

Run:

```bash
./scripts/aiops-traced-config-crashloop.sh apply
```

Expected: 目标 Pod 的 waiting reason 为 `CrashLoopBackOff`，上一轮 reason 为 `Error`，
exit code 为 `78`。

- [ ] **Step 2: 验证日志和服务拓扑前置条件**

Run:

```bash
./scripts/aiops-traced-config-crashloop.sh verify
```

Expected: previous logs 含 `config_missing`、`PAYMENT_GATEWAY_TOKEN`、`trace_id`、
`span_id`，Driver 日志含 HTTP 500 和 `traceparent`，Service endpoint 关联目标 Pod。

### Task 3: 实时 MCP 和 Robusta 泛化审计

**Files:**
- Modify only if runtime evidence exposes a generic defect:
  `../mcpstander/servers/aiops_observability/`
- Modify only if runtime evidence exposes a generic defect:
  `app/core/context/observation.py`
- Modify only if runtime evidence exposes a generic defect:
  `app/core/workflow/nodes/evidence_collector.py`
- Modify only if runtime evidence exposes a generic defect:
  `app/core/workflow/nodes/conclusion_formatter.py`

- [ ] **Step 1: 调用现有 coarse MCP**

以实际 Pod 名调用 `collect_aiops_case(namespace, pod, scenario="auto")`，检查
`dimension_details`、evidence refs、coverage 和 topology。

- [ ] **Step 2: 运行 Robusta `/ask`**

Run:

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=请诊断 namespace aiops-traced-config 中 Pod <pod> 的异常，使用真实 metrics、logging、tracing 和 topology 证据说明根因。"
```

Expected: Qwen 自主调用实时 AIOps MCP，报告引用 Error/exit 78、HTTP 500、缺失配置日志、
Trace 和拓扑边，不得判断为 OOM。

- [ ] **Step 3: 只在失败时修复通用逻辑**

新增测试先复现真实缺陷，再做最小修改；禁止按 Pod 名、namespace 或
`config_missing` 场景硬编码 collector 分支。

- [ ] **Step 4: 批量回归**

Run:

```bash
.venv/bin/pytest -q tests/unit/test_aiops_traced_config_testcase.py tests/unit/aicall tests/unit/workflow
```

Expected: 全部通过。
