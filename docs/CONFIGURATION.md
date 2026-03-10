# 配置指南

---

## 配置文件位置

| 环境 | 配置文件 | 说明 |
|------|----------|------|
| 本地开发 | `config/config.yaml` | 直接修改即可 |
| K8s 部署 | `deploy/configmap/config.yaml` | ConfigMap，`make deploy` 后生效 |
| K8s 敏感配置 | `deploy/secrets/core.yaml` | Secret，存放 API Key 等 |
| K8s 部署清单 | `deploy/k8s-simple.yaml` | Deployment + Service 定义 |

---

## 1. LLM 提供商配置

### 配置优先级

```
Secret 环境变量（LLM_API_KEY / LLM_MODEL / LLM_API_BASE）
        ↓ 为空则回退
config.yaml llm 块（llm.api_key / llm.model / llm.api_base）
        ↓ 为空则回退
默认值（model = "deepseek/deepseek-chat"）
```

### 通过 Secret 配置（推荐）

修改 `deploy/secrets/core.yaml`：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aiops-secret
  namespace: aiops
type: Opaque
stringData:
  LLM_API_KEY: "sk-xxx"
  LLM_MODEL: "deepseek/deepseek-chat"
  LLM_API_BASE: ""                      # 留空使用默认端点
```

### 通过 config.yaml 配置

在 `deploy/configmap/config.yaml` 中：

```yaml
llm:
  model: "deepseek/deepseek-chat"
  # api_key: "sk-xxx"                   # 留空则从 LLM_API_KEY 环境变量读取
  # api_base: ""                        # 留空使用默认端点
```

### 支持的 LLM 提供商

| 提供商 | LLM_MODEL | LLM_API_BASE | 说明 |
|--------|-----------|--------------|------|
| DeepSeek | `deepseek/deepseek-chat` | 留空 | 默认提供商 |
| Claude | `anthropic/claude-sonnet-4-6` | `https://terminal.pub` | 需要代理端点 |
| GLM 智谱 | `openai/glm-4` | `https://open.bigmodel.cn/api/paas/v4` | OpenAI 兼容模式 |
| OpenAI | `openai/gpt-4o` | 留空 | 直连 OpenAI |

模型 ID 格式遵循 [litellm 规范](https://docs.litellm.ai/docs/providers)：`提供商前缀/模型名`。

### 切换提供商示例

从 DeepSeek 切换到 Claude：

```yaml
# deploy/secrets/core.yaml
stringData:
  LLM_API_KEY: "sk-3McMrIRSpOZD13ugOrSJe6zNAfpMz5YdGa6bHhh2tjqEj3tp"
  LLM_MODEL: "anthropic/claude-sonnet-4-6"
  LLM_API_BASE: "https://terminal.pub"
```

然后重新部署：`make delete && make deploy-master`

---

## 2. 工具集配置

### 内置工具集

在 `toolsets` 块中配置：

```yaml
toolsets:
  # K8s 只读操作（kubectl get/describe/events 等）
  kubernetes/core:
    enabled: true

  # Helm 只读操作
  helm/core:
    enabled: true

  # Bash 命令执行（需配合 BASH_TOOL_UNSAFE_ALLOW_ALL）
  bash:
    enabled: true

  # Prometheus 查询
  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: "http://observability-prometheus.xnet.svc:9090"

  # Runbook 知识库
  runbook:
    enabled: true

  # 网页抓取
  internet:
    enabled: true

  # TCP 连通性检查
  connectivity_check:
    enabled: true
```

### MCP 工具集（远程 SSE）

在 `mcp_servers` 块中配置：

```yaml
mcp_servers:
  elasticsearch:
    description: "Elasticsearch MCP - 查询索引、搜索日志"
    config:
      url: "http://mcp-server-manager.mcp.svc.cluster.local:8088/sse"
      mode: "sse"
    enabled: true

  k8s-mcp-service:
    description: "K8s MCP - 查询 K8s 资源"
    config:
      url: "http://mcp-server-manager.mcp.svc.cluster.local:8093/sse"
      mode: "sse"
    enabled: true

  # 添加新 MCP 工具
  my-custom-tool:
    description: "工具描述（AI 根据此描述判断何时调用）"
    config:
      url: "http://my-server:8099/sse"
      mode: "sse"
    llm_instructions: "可选：给 AI 的使用说明"
    enabled: true
```

**说明**：`description` 是 AI 判断何时调用工具的依据，应清晰描述工具能力。

---

## 3. 联邦查询（多集群）配置

### 主集群配置

```yaml
federation:
  enabled: true                          # 主集群设为 true
  max_tokens_per_agent: 0                # 子集群报告压缩阈值（0=不压缩）
  synthesis_timeout: 300                  # 等待子集群响应超时（秒）
  sub_agents:
    # 主集群本身
    - name: "main"
      url: "http://localhost:8000"        # 容器内端口，不能用 NodePort
      description: "主集群"
      enabled: true
    # 子集群
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"      # 子集群 NodePort
      description: "子集群 24"
      enabled: true
```

### 子集群配置

```yaml
federation:
  enabled: false                          # 子集群设为 false
```

### 关键注意事项

- 主集群的 `url` 必须是 `http://localhost:8000`（容器内端口），**不能** 用 `http://localhost:30800`
- 子集群使用 `NodePort 30800`（宿主机 IP + 端口）
- 设置 `enabled: false` 可临时禁用某个子集群
- `name` 字段用于 A2A 路由（用户可在问题中引用集群名）

### 部署命令

```bash
make build push deploy-master    # 主集群：自动设置 federation.enabled=true
make build push deploy-slave     # 子集群：自动设置 federation.enabled=false
```

---

## 4. 执行模式配置

| 模式 | 配置 | 说明 |
|------|------|------|
| HolmesGPT（默认） | `USE_WORKFLOW=false` | LLM 自主规划工具调用，灵活但不确定 |
| LangGraph 工作流 | `USE_WORKFLOW=true` | 四阶段流水线（定层→采证→根因→报告），流程确定 |

在 `deploy/secrets/core.yaml` 中配置：

```yaml
stringData:
  USE_WORKFLOW: "true"    # 或 "false"
```

---

## 5. 完整环境变量参考

| 变量 | 默认值 | 来源 | 说明 |
|------|--------|------|------|
| `LLM_API_KEY` | — | Secret | LLM API Key |
| `LLM_MODEL` | — | Secret | 覆盖 config.yaml 中的 model |
| `LLM_API_BASE` | — | Secret | API 端点覆盖 |
| `USE_WORKFLOW` | `false` | Secret | 启用工作流模式 |
| `BASH_TOOL_UNSAFE_ALLOW_ALL` | `false` | Secret | 允许所有 bash 命令 |
| `CONFIG_FILE` | 自动检测 | Deployment env | 配置文件路径 |
| `API_HOST` | `0.0.0.0` | — | 服务监听地址 |
| `API_PORT` | `8000` | — | 服务监听端口 |
| `METRICS_MTTR_THRESHOLD` | `600` | Secret | MTTR 阈值（秒） |
| `METRICS_RCA_CONFIDENCE_THRESHOLD` | `0.8` | Secret | 根因置信度阈值 |
| `METRICS_EVIDENCE_THRESHOLD` | `0.9` | Secret | 证据完整率阈值 |

所有 Secret 环境变量均为 `optional: true`，缺失不会导致 Pod 启动失败。

---

## 6. Runbook 知识库配置

Runbook 存放在 `knowledge_base/runbooks/` 目录：

```
knowledge_base/runbooks/
├── catalog.json            # 索引（title + description，AI 用于匹配）
├── oomkilled.md            # OOMKilled 处理
├── disk_full.md            # 磁盘满处理
├── crashloop.md            # CrashLoopBackOff 处理
└── ...
```

**添加新 Runbook**：

1. 创建 `.md` 文件
2. 在 `catalog.json` 注册：
```json
{
  "items": [
    {
      "title": "新故障处理指南",
      "description": "故障场景描述（AI 用此匹配）",
      "path": "new_runbook.md"
    }
  ]
}
```
3. K8s 部署需更新 `deploy/configmap/runbooks.yaml` 并重新部署
