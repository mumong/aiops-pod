# Holmes 内置工具实现说明（用于自建 MCP 替代）

本文档从 Holmes 源码中提取 **run_bash_command、get_prometheus_target、internet（fetch_webpage）、prometheus/metrics** 的接口与实现方式，便于你用本地 MCP 服务复刻相同语义。  
格式与 MCP 的 `list_tools()` 一致：`name`、`description`、`inputSchema`，并补充「调用/实现方式」。

---

## 1. run_bash_command

**来源**：`holmes/plugins/toolsets/bash/bash_toolset.py`（RunBashCommand）  
**执行**：`holmes/plugins/toolsets/bash/common/bash.py` 中 `execute_bash_command(cmd, timeout, params)`，内部用 `subprocess.run(protected_cmd, shell=True, executable="/bin/bash", timeout=timeout)`，返回 stdout+stderr 与 returncode。

### MCP 工具定义

```python
Tool(
    name="run_bash_command",
    description="Executes a given bash command and returns its standard output, standard error, and exit code. The command is executed via 'bash -c \"<command>\"'. Only some commands are allowed.",
    inputSchema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command string to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Optional timeout in seconds for the command execution. Defaults to 60."
            }
        },
        "required": ["command"]
    }
)
```

### 实现方式

- **入参**：`command`（必填）、`timeout`（可选，默认 60）。
- **调用**：在宿主机上执行 `bash -c "<command>"`（Holmes 会加 ulimit 等前缀，你可按需简化）。
- **返回**：成功时返回「命令 + 标准输出」的文本；失败时返回错误信息与 `returncode`（非 0）。超时则报错。
- **注意**：Holmes 内置会对 `command` 做白名单/安全校验（`make_command_safe`），MCP 侧建议自己做命令限制或审批。

---

## 2. get_prometheus_target

**来源**：`holmes/plugins/toolsets/kubernetes.yaml` 中 `kubernetes/kube-prometheus-stack`，YAML 定义的 command 工具。

### MCP 工具定义

```python
Tool(
    name="get_prometheus_target",
    description="Fetch the definition of a Prometheus target",
    inputSchema={
        "type": "object",
        "properties": {
            "prometheus_namespace": {
                "type": "string",
                "description": "Kubernetes namespace where Prometheus Service runs"
            },
            "prometheus_service_name": {
                "type": "string",
                "description": "Prometheus Service name (e.g. prometheus-server)"
            },
            "target_name": {
                "type": "string",
                "description": "Prometheus job label value to filter (e.g. kubernetes-pods)"
            }
        },
        "required": ["prometheus_namespace", "prometheus_service_name", "target_name"]
    }
)
```

### 实现方式

- **原始实现**：在集群内执行下面这条命令（模板渲染后）：
  ```bash
  kubectl get --raw '/api/v1/namespaces/{{prometheus_namespace}}/services/{{prometheus_service_name}}:9090/proxy/api/v1/targets' | jq '.data.activeTargets[] | select(.labels.job == "{{ target_name }}")'
  ```
- **含义**：通过 K8s API 访问 Prometheus 的 `/api/v1/targets`，再按 `job` 标签过滤出指定 target。
- **MCP 实现思路**：  
  - 若 MCP 跑在集群内：可照旧用 `kubectl get --raw` + 上述 URL + jq；或写脚本/HTTP 调 Prometheus 的 `api/v1/targets`，再在内存里按 `labels.job == target_name` 过滤。  
  - 若 MCP 在集群外：用可访问的 Prometheus 地址直接 `GET {prometheus_url}/api/v1/targets`，再按 `target_name`（job）过滤返回。

---

## 3. internet（fetch_webpage）

**来源**：`holmes/plugins/toolsets/internet/internet.py`（InternetToolset 下只有 FetchWebpage 一个工具；toolset 名为 `internet`，工具名为 `fetch_webpage`）。

### MCP 工具定义

```python
Tool(
    name="fetch_webpage",
    description="Fetch a webpage. Use this to fetch runbooks if they are present before starting your investigation (if no other tool like confluence is more appropriate).",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch"
            }
        },
        "required": ["url"]
    }
)
```

### 实现方式

- **入参**：`url`（必填）。
- **调用**：
  1. 使用自定义 User-Agent（如 `Mozilla/5.0 ...`）对 `url` 发 **HTTP GET**，超时约 5 秒（Holmes 用 `INTERNET_TOOLSET_TIMEOUT_SECONDS`）。
  2. 若响应是 HTML（`Content-Type: text/html` 或内容形如 `<!DOCTYPE html`）：用 BeautifulSoup 去掉 script/style/广告等，再转成 **Markdown**（markdownify）返回。
  3. 非 HTML 则直接返回响应文本。
- **返回**：成功返回（可能转成 Markdown 的）页面正文；失败返回错误信息。
- **可选**：支持配置 `additional_headers`（如 Authorization），MCP 可做同名参数或配置项。

---

## 4. prometheus/metrics

**来源**：`holmes/plugins/toolsets/prometheus/prometheus.py`（PrometheusToolset，name 为 `prometheus/metrics`）。  
所有请求都发往配置中的 `prometheus_url`（如 `http://observability-prometheus.xnet.svc:9090`），并支持 `verify_ssl`、`headers` 等。

下面 8 个工具都按「MCP 工具定义 + 实现方式」列出，便于你逐个做成 MCP tools。

---

### 4.1 list_prometheus_rules

```python
Tool(
    name="list_prometheus_rules",
    description="List all defined Prometheus rules (api/v1/rules). Will show the Prometheus rules description, expression and annotations",
    inputSchema={"type": "object", "properties": {}}
)
```

- **实现**：`GET {prometheus_url}/api/v1/rules`，返回 body 中的 `data` 即可（规则列表）。

---

### 4.2 get_metric_names

```python
Tool(
    name="get_metric_names",
    description="Get list of metric names using /api/v1/label/__name__/values. FASTEST method for metric discovery. Use match[] to filter (e.g. {__name__=~\"node_cpu.*\"}). Returns up to 100 names; use more specific match if truncated.",
    inputSchema={
        "type": "object",
        "properties": {
            "match": {"type": "string", "description": "PromQL selector, e.g. {__name__=~\"node_cpu.*|node_memory.*\"}"},
            "start": {"type": "string", "description": "Start time RFC3339 or Unix. Default: 1 hour ago"},
            "end": {"type": "string", "description": "End time RFC3339 or Unix. Default: now"}
        },
        "required": ["match"]
    }
)
```

- **实现**：`GET {prometheus_url}/api/v1/label/__name__/values`，query 参数：`match[]=...`，可选 `start`、`end`。返回 `data` 数组（指标名列表）。

---

### 4.3 get_label_values

```python
Tool(
    name="get_label_values",
    description="Get all values for a specific label using /api/v1/label/{label}/values. E.g. label=pod, namespace, job.",
    inputSchema={
        "type": "object",
        "properties": {
            "label": {"type": "string", "description": "Label name (e.g. pod, namespace, job, instance)"},
            "match": {"type": "string", "description": "Optional PromQL selector"},
            "start": {"type": "string"},
            "end": {"type": "string"}
        },
        "required": ["label"]
    }
)
```

- **实现**：`GET {prometheus_url}/api/v1/label/{label}/values`，query：可选 `match[]`、`start`、`end`。

---

### 4.4 get_all_labels

```python
Tool(
    name="get_all_labels",
    description="Get list of all label names using /api/v1/labels. Optional match[] to filter.",
    inputSchema={
        "type": "object",
        "properties": {
            "match": {"type": "string"},
            "start": {"type": "string"},
            "end": {"type": "string"}
        }
    }
)
```

- **实现**：`GET {prometheus_url}/api/v1/labels`，query：可选 `match[]`、`start`、`end`。

---

### 4.5 get_series

```python
Tool(
    name="get_series",
    description="Get time series using /api/v1/series. Returns label sets for series matching the selector. Requires match[].",
    inputSchema={
        "type": "object",
        "properties": {
            "match": {"type": "string", "description": "PromQL selector e.g. up or {job=\"prometheus\"}"},
            "start": {"type": "string"},
            "end": {"type": "string"}
        },
        "required": ["match"]
    }
)
```

- **实现**：`GET {prometheus_url}/api/v1/series`，query：`match[]`（必填）、`start`、`end`。

---

### 4.6 get_metric_metadata

```python
Tool(
    name="get_metric_metadata",
    description="Get metric metadata (type, help, unit) using /api/v1/metadata. Optional metric name to filter.",
    inputSchema={
        "type": "object",
        "properties": {
            "metric": {"type": "string", "description": "Optional metric name to filter"}
        }
    }
)
```

- **实现**：`GET {prometheus_url}/api/v1/metadata`，query：可选 `metric`。

---

### 4.7 execute_prometheus_instant_query

```python
Tool(
    name="execute_prometheus_instant_query",
    description="Execute an instant PromQL query (single point in time). Default timeout 20s, max 180s.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The PromQL query"},
            "description": {"type": "string", "description": "Describes the query (for logging)"},
            "timeout": {"type": "number", "description": "Query timeout in seconds"}
        },
        "required": ["query", "description"]
    }
)
```

- **实现**：`POST {prometheus_url}/api/v1/query`，body `{"query": "<PromQL>"}`。返回 Prometheus 标准 JSON；Holmes 会取 `data` 并可能做摘要。

---

### 4.8 execute_prometheus_range_query

```python
Tool(
    name="execute_prometheus_range_query",
    description="Execute a PromQL range query (time range). Default last 1 hour. output_type: Plain | Bytes | Percentage | CPUUsage.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "description": {"type": "string"},
            "start": {"type": "string", "description": "RFC3339 or Unix"},
            "end": {"type": "string"},
            "step": {"type": "number", "description": "Step width in seconds"},
            "output_type": {"type": "string", "description": "Plain | Bytes | Percentage | CPUUsage"},
            "timeout": {"type": "number"},
            "max_points": {"type": "number"}
        },
        "required": ["query", "description", "output_type"]
    }
)
```

- **实现**：`POST {prometheus_url}/api/v1/query_range`，body：`query`、`start`、`end`、`step`。返回 `data`；`output_type` 用于后续展示转换（字节、百分比、CPU 核数等），可在 MCP 内或客户端做。

---

## 小结

| 工具 | 类型 | 核心实现 |
|------|------|----------|
| run_bash_command | 本地执行 | `subprocess.run(["bash", "-c", command], timeout=timeout)`，返回 stdout/returncode |
| get_prometheus_target | K8s + Prometheus | 访问 Prometheus `api/v1/targets`，按 job 过滤；或 kubectl proxy 到该 API |
| fetch_webpage (internet) | HTTP | GET url → 若 HTML 则清理并转 Markdown，否则返回原文 |
| prometheus/metrics 下 8 个 | HTTP | 全部为对 `{prometheus_url}/api/v1/...` 的 GET/POST，参数与上表一致 |

你在 MCP 的 `list_tools()` 里返回上述 `name`/`description`/`inputSchema`，在 `call_tool` 里按「实现方式」调用后端（bash、Prometheus API、HTTP 抓页），即可在行为上替代这些内置工具。
