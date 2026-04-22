# K8s AIOps Copilot

面向私有化 Kubernetes 环境的智能诊断与查询服务。

当前正式设计已经收敛为两条单集群主链路：

- `/ask`：诊断入口，走 4 节点工作流 `layer -> evidence -> rca -> conclusion`
- `/query`：查询入口，走 2 节点工作流 `layer -> conclusion`

并提供两类联邦入口：

- `/federation/ask`、`/federation/ask/v2`
- `/federation/query`、`/federation/query/v2`

## 核心特点

- 查询与诊断彻底分流：简单查询不再走完整诊断链路
- 当前态优先：不把历史 event 直接当成当前故障
- 多 Runbook 参考：广义健康检查可先看通用基线，再按信号继续抓场景 runbook
- MCP 工具驱动：Kubernetes、Prometheus、Bash、Helm 等能力通过 MCP 接入
- 流式可观测：终端可直接看到节点进度、工具调用和最终报告
- 联邦多集群：支持广播模式和 Agent-to-Agent 智能路由模式

## 工作流

### `/ask`

用于“分析原因、诊断故障、现在有什么问题”这类问题。

1. `layer`
   定位问题层级，产出 `HEALTHY / L0-L4`
2. `evidence`
   制定证据计划并调用工具采集真实数据
3. `rca`
   基于证据做根因分析，产出 `primary_runbooks`
4. `conclusion`
   汇总成最终诊断报告

### `/query`

用于“CPU/内存/磁盘/状态/列表/某项指标是多少”这类问题。

1. `layer`
   判断为 `QUERY`，直接调工具并产出结构化 `query_result`
2. `conclusion`
   直接渲染 `query_result`

## 快速开始

### 本地运行

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 准备 LLM 环境变量
也可以在配置文件/deploy/secrets/core.yaml下编辑配置
```bash
export LLM_API_KEY="your-key"
export LLM_MODEL="deepseek/deepseek-chat"
export LLM_API_BASE=""
```

3. 启动服务

```bash
python run.py
```

4. 验证

```bash
curl http://127.0.0.1:8000/health
```

### Kubernetes 部署

1. 编辑 [deploy/secrets/core.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/secrets/core.yaml)
2. 编辑 [deploy/configmap/config.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml)
3. 构建并推镜像

```bash
make build
make push
```

4. 部署

```bash
# 单集群/普通部署
make deploy

# 主集群（开启 federation）
make deploy-master

# 子集群（关闭 federation）
make deploy-slave
```

5. 查看状态

```bash
make logs
curl http://<node-ip>:30800/health
```

### 卸载 / 运维

```bash
# 删除资源，保留 namespace
make delete

# 重启
make restart

# 查看日志
make logs
```

## 常用 API

### 单集群诊断

```bash
curl --no-buffer -G "http://HOST:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？"
```

### 单集群查询

```bash
curl --no-buffer -G "http://HOST:30800/query" \
  --data-urlencode "q=集群 CPU 和内存使用率是多少，具体到每个 node"
```

### 联邦诊断

```bash
curl --no-buffer -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=main 集群和 cluster-24 现在分别有什么问题？"
```

### 联邦查询

```bash
curl --no-buffer -G "http://HOST:30800/federation/query/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU 使用率"
```

## API 设计

| 端点 | 用途 | 正式推荐 |
|------|------|----------|
| `/ask` | 单集群诊断 | 是 |
| `/query` | 单集群查询 | 是 |
| `/federation/ask` | 多集群广播诊断 | 是 |
| `/federation/query` | 多集群广播查询 | 是 |
| `/federation/ask/v2` | 多集群 Agent 诊断 | 是 |
| `/federation/query/v2` | 多集群 Agent 查询 | 是 |
| `/health` | 健康检查 | 是 |
| `/tools` | 工具列表 | 调试 |
| `/runbooks` | Runbook 列表 | 调试 |
| `/reports` | 查看已保存报告 | 调试 |
| `/api/v1/query` | 兼容旧接口 | 否 |
| `/api/v1/query/stream` | 兼容旧接口 | 否 |
| `/q/{question}` | 快捷别名 | 否 |

## 核心配置

正式配置文件是 [deploy/configmap/config.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml)。

### `llm`

```yaml
llm:
  model: "deepseek/deepseek-chat"
```

- 主要由 Secret 环境变量覆盖：`LLM_API_KEY`、`LLM_MODEL`、`LLM_API_BASE`


### `mcp_servers`

- 定义所有外部能力入口
- 当前主力能力都通过 MCP 提供
- `description` 很重要，会影响模型是否会选中该工具

### `workflow`

```yaml
workflow:
  rca_mode: lite
  nodes:
    layer: true
    evidence: true
    rca: true
    conclusion: true
  max_steps:
    layer: 28
    evidence: 30
    rca: 0
    conclusion: 0
```

- `rca_mode`
  - `lite`：RCA 不重复调工具，只基于已有证据分析
  - `full`：RCA 允许继续工具调用
- `nodes`
  - 控制默认工作流节点开关
  - `/ask` 和 `/query` 仍会按各自路由做覆盖
- `max_steps`
  - 控制节点工具调用上限

### `metrics`

- 控制是否展示质量指标、阈值和权重
- 当前默认 `enabled: false`，因此默认只展示性能统计和诊断追踪

### `federation`

```yaml
federation:
  enabled: true
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"
      enabled: true
```

- 主集群开启，子集群关闭
- `url` 需要指向子集群可访问的服务地址

## 部署文件

- [deploy/k8s-simple.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/k8s-simple.yaml)
  Deployment + Service
- [deploy/configmap/config.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml)
  主配置
- [deploy/configmap/runbooks.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/runbooks.yaml)
  Runbook 知识库
- [deploy/secrets/core.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/secrets/core.yaml)
  LLM 与运行时 Secret
- [deploy/rbac.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/rbac.yaml)
  ServiceAccount / RBAC
