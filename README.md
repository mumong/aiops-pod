# 🤖 K8s-SRE Agent

基于 [HolmesGPT](https://github.com/robusta-dev/holmesgpt) 的智能 Kubernetes 运维诊断 Agent，采用**分层诊断模型**快速定位问题根因。

**当前版本**: `2.8.4`

---

## 🎯 核心能力

```
分层定位问题 → 分类识别原因 → 给出证据支撑的结论
```

| 能力 | 说明 |
|------|------|
| 🏗️ **分层诊断** | 基于 L0-L4 五层架构模型，快速定位问题层级 |
| 🔍 **证据驱动** | 每个结论都有明确的证据来源 |
| 📚 **Runbook 知识库** | 19+ 内置故障诊断手册，覆盖常见场景 |
| 🛠️ **智能修复** | 识别根因后自动执行安全的修复操作 |
| 🔌 **MCP 扩展** | 支持 Helm、Prometheus、Elasticsearch 等工具集成 |

---

## 🏗️ 五层诊断模型

问题分析遵循 **L0-L4 分层架构**，从底层向上逐层排查：

```
┌─────────────────────────────────────────────────────────────────┐
│ L4: 应用层 (Application)                                        │
│     业务逻辑错误、代码异常、配置错误、依赖服务不可用              │
├─────────────────────────────────────────────────────────────────┤
│ L3: 服务与网络层 (Service & Network)                             │
│     Service/Ingress 配置、DNS 解析、NetworkPolicy、跨 Pod 通信   │
├─────────────────────────────────────────────────────────────────┤
│ L2: 工作负载层 (Workload)                                        │
│     Pod 生命周期、容器状态、镜像拉取、探针、资源限制              │
├─────────────────────────────────────────────────────────────────┤
│ L1: 集群与节点层 (Cluster & Node)                                │
│     Node 状态、调度器、kubelet、容器运行时、系统资源              │
├─────────────────────────────────────────────────────────────────┤
│ L0: 基础设施层 (Infrastructure)                                  │
│     磁盘、内存、CPU、网络连通性、内核、文件系统                   │
└─────────────────────────────────────────────────────────────────┘
```

### 诊断输出示例

```
## 📍 问题定位
- **层级**: L2 - 工作负载层
- **分类**: Pod CrashLoop
- **置信度**: 高

## 🔍 现象描述
Pod nginx-xxx 处于 CrashLoopBackOff 状态，已重启 15 次

## 🕵️ 根因分析
| 证据来源 | 关键信息 | 说明 |
|----------|----------|------|
| kubectl describe pod | Exit Code 137 | 容器被 OOMKilled |
| kubectl logs --previous | "Out of memory" | 应用内存溢出 |

**结论**: 容器内存 limit 设置过小(512Mi)，应用实际需要更多内存

## 🛠️ 修复建议
1. 增加 resources.limits.memory 到 1Gi
2. 检查应用是否存在内存泄漏
```

---

## 🚀 快速使用

### 部署后调用 API

```bash
# 🔥 最简单的方式（推荐）
curl -X POST "http://<NODE_IP>:30800/ask" -d "q=Pod 一直在重启"

# 中文问题（GET 方式需要 URL 编码）
curl -G "http://<NODE_IP>:30800/ask" --data-urlencode "q=磁盘满了怎么清理"

# 调整最大步数（复杂问题）
curl -X POST "http://<NODE_IP>:30800/ask" -d "q=安装 observability" -d "max_steps=50"
```

### 可用端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/ask` | GET/POST | 主要查询入口 |
| `/health` | GET | 健康检查 |
| `/tools` | GET | 可用工具列表 |
| `/tools/detail` | GET | 工具详情（按 toolset 分组，含 schema/描述，便于二次开发） |
| `/runbooks` | GET | 可用 Runbooks |
| `/api/v1/mcp/status` | GET | MCP 服务器状态 |
| `/artifacts/{artifact_id}` | GET | 拉取被截断的大输出全文（TTL 内有效） |

### API 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | 必填 | 问题内容 |
| `stream` | bool | true | 是否流式输出 |
| `format` | string | text | 输出格式: text(人类可读)/sse(结构化事件流，推荐) |
| `max_steps` | int | 20 | 最大执行步数 (1-100) |

### ✅ 推荐：使用结构化 SSE（可稳定看到每一步 + 一定有最终结果）

```bash
curl -N -G "http://<NODE_IP>:30800/ask" \
  --data-urlencode "q=我的集群有什么问题" \
  --data-urlencode "format=sse"
```

SSE 会持续输出 `event: <type>` / `data: {...}`，关键事件：
- `tool_start` / `tool_result`：每次工具调用（若结果过长会带 `artifact_id`）
- `iteration_end`：每轮迭代结束的 token/耗时
- `blocked`：被安全策略阻塞（例如需要批准）
- `error`：执行错误
- `final`：**最终结论（保证一定出现，且不会把 DSML 片段当最终答案）**

如 `tool_result.result_truncated=true` 且带 `artifact_id`，可拉取全文：

```bash
curl "http://<NODE_IP>:30800/artifacts/<artifact_id>"
```

---

## ☸️ K8s 部署

### 一键部署

```bash
# 1. 配置 API Key（必须）
vim deploy/secrets/core.yaml    # 填入 DEEPSEEK_API_KEY

# 2. 构建、推送、部署
make build push deploy

# 3. 查看日志
make logs
```

### 部署文件说明

```
deploy/
├── k8s-simple.yaml           # Deployment + Service (NodePort: 30800)
├── rbac.yaml                 # ServiceAccount + ClusterRole
├── configmap/
│   ├── config.yaml           # 应用配置（工具集/MCP）
│   └── runbooks.yaml         # Runbook 知识库
└── secrets/
    └── core.yaml             # API Key 等敏感信息
```

### Makefile 命令

| 命令 | 说明 |
|------|------|
| `make build` | 构建 Docker 镜像 |
| `make push` | 推送到镜像仓库 |
| `make deploy` | 部署到 K8s（自动同步版本） |
| `make delete` | 删除部署（保留 namespace） |
| `make restart` | 重启 Pod（刷新 ConfigMap） |
| `make logs` | 查看实时日志 |

---

## 📚 Runbook 知识库

内置 **19+ 故障诊断手册**，按分层模型组织，AI 会自动参考：

### L0: 基础设施层

| Runbook | 说明 |
|---------|------|
| `infra-disk-full` | 磁盘空间耗尽 - 日志膨胀、Docker 镜像堆积、Inode 耗尽 |
| `infra-memory-exhausted` | 系统内存耗尽 - OOM Killer、内存泄漏 |
| `infra-cpu-saturation` | CPU 饱和 - 高 load average、IO Wait |

### L1: 集群与节点层

| Runbook | 说明 |
|---------|------|
| `node-not-ready` | 节点异常 NotReady - kubelet、容器运行时 |
| `node-disk-pressure` | 节点磁盘压力 - DiskPressure 条件 |
| `node-memory-pressure` | 节点内存压力 - MemoryPressure 条件 |

### L2: 工作负载层

| Runbook | 说明 |
|---------|------|
| `pod-quick-diagnosis` | Pod 异常快速诊断入口（流程型） |
| `pod-pending` | Pod 调度失败 - 资源不足、污点、PVC |
| `pod-image-pull-failed` | 镜像拉取失败 - 地址、网络、认证 |
| `pod-crashloop-backoff` | 容器崩溃循环 - Exit Code 解读、OOM |
| `pod-not-ready` | Pod 未就绪 - 健康检查失败 |
| `pod-terminating` | Pod 删除卡住 - Finalizer 阻塞 |
| `pod-evicted` | Pod 被驱逐 - 节点资源压力 |

### L3: 服务与网络层

| Runbook | 说明 |
|---------|------|
| `service-no-endpoints` | Service 无后端 - Selector 不匹配 |
| `dns-resolution-failed` | DNS 解析失败 - CoreDNS 异常 |
| `network-connectivity` | 网络连通性 - Pod 间通信、CNI |
| `ingress-not-working` | Ingress 无法访问 - 404/502/503 |

### L4: 应用层

| Runbook | 说明 |
|---------|------|
| `app-connection-refused` | 应用连接被拒绝 - 数据库/缓存/MQ |
| `app-5xx-errors` | 应用 5xx 错误 - 500/502/503/504 |
| `app-config-errors` | 应用配置错误 - 环境变量、ConfigMap |

### 操作类

| Runbook | 说明 |
|---------|------|
| `helm-observability-install` | Helm 管理可观测性平台（流程型） |

### Runbook 类型说明

- **知识型 (knowledge)**: 提供诊断知识和参考，可灵活运用
- **流程型 (procedure)**: 包含明确操作步骤，严格按流程执行

### 更新 Runbook

```bash
# 编辑 ConfigMap
kubectl edit configmap aiops-runbooks -n aiops

# 或修改文件后重新部署
vim deploy/configmap/runbooks.yaml
make restart
```

---

## 🔌 MCP 工具集

### 内置工具

| 工具集 | 说明 |
|--------|------|
| `kubernetes/core` | kubectl 命令封装 |
| `prometheus/metrics` | Prometheus 查询 |
| `bash` | 安全的 bash 命令 |

### 外部 MCP 服务器

通过 `config.yaml` 配置外部 MCP 服务器：

```yaml
mcp_servers:
  helmcharts:
    config:
      url: "http://mcp-helm:8083/sse"
      mode: "sse"
    enabled: true
  
  elasticsearch:
    config:
      url: "http://mcp-server:8082/sse"
      mode: "sse"
    enabled: true
```

---

## 📁 项目结构

```
├── app/
│   ├── api/routes.py           # FastAPI 路由
│   ├── core/
│   │   ├── service.py          # 核心服务（⭐重点）
│   │   ├── prompts.py          # System Prompt（分层诊断模型）
│   │   ├── mcp/manager.py      # MCP 本地 auto-start 管理（默认关闭）
│   │   ├── holmes/             # Holmes 相关能力拆分（配置/流式/日志等）
│   │   └── runbook.py          # Runbook 加载
│   └── main.py                 # 应用入口
├── deploy/                     # K8s 部署文件
│   ├── configmap/runbooks.yaml # Runbook 知识库（19+ 手册）
│   └── secrets/core.yaml       # API Key
├── config/config.yaml          # 本地开发配置
├── Dockerfile                  # 容器镜像
├── Makefile                    # 构建/部署脚本
├── VERSION                     # 版本号
└── requirements.txt            # Python 依赖
```

---

## 🔧 本地开发

```bash
# 1. 创建虚拟环境
python3 -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
export DEEPSEEK_API_KEY="your-api-key"
export CONFIG_FILE="config/config.yaml"

# 4. 启动服务
python run.py

# 5. 测试
curl -X POST "http://localhost:8000/ask" -d "q=检查集群状态"
```

---

## 🔐 安全配置

### 敏感信息位置

| 文件 | 内容 | 说明 |
|------|------|------|
| `deploy/secrets/core.yaml` | DEEPSEEK_API_KEY | LLM API 密钥 |
| `deploy/secrets/core.yaml` | DEEPSEEK_MODEL | 使用的模型 (deepseek-reasoner) |
| `deploy/configmap/runbooks.yaml` | Helm Repo 凭证 | observability 私有仓库 |

### 安全建议

- ⚠️ 不要将真实密钥提交到 Git
- 使用 `.gitignore` 忽略 `deploy/secrets/*.yaml`
- 生产环境使用 Kubernetes Secrets 或外部密钥管理

---

## 📊 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户请求                                │
│                 curl /ask?q="Pod 一直重启"                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                       HolmesGPT 引擎                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  SYSTEM_PROMPT (分层诊断模型 L0-L4)                          │  │
│  │  + Runbooks (故障知识库)                                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬───────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┬───────────────┐
            ▼               ▼               ▼               ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ kubectl  │   │Prometheus│   │  Helm    │   │   Bash   │
      │  工具    │   │  查询    │   │ (MCP)    │   │  命令    │
      └──────────┘   └──────────┘   └──────────┘   └──────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                       结构化诊断输出                               │
│   📍 问题定位 (层级 + 分类 + 置信度)                               │
│   🔍 现象描述                                                      │
│   🕵️ 根因分析 (证据来源 + 关键信息)                                │
│   🛠️ 修复建议                                                      │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🤝 致谢

- [HolmesGPT](https://github.com/robusta-dev/holmesgpt) - AI 故障诊断引擎
- [DeepSeek](https://www.deepseek.com/) - LLM 提供商
