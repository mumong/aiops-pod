# 部署与使用指南

---

## 一、部署

### LLM 配置

修改 `deploy/secrets/core.yaml`：

```yaml
stringData:
  LLM_API_KEY: "sk-xxx"
  LLM_MODEL: "deepseek/deepseek-chat"     # 或 anthropic/claude-sonnet-4-6
  LLM_API_BASE: ""                          # DeepSeek 留空，Claude 填代理地址
  USE_WORKFLOW: "true"                      # 启用工作流模式
```

### 主集群部署

```bash
make build push deploy-master
```

### 子集群部署

```bash
make build push deploy-slave
```

### 运维命令

```bash
make logs        # 查看日志
make restart     # 重启
make delete      # 删除（保留 namespace）
```

### 联邦查询配置

主集群 `deploy/configmap/config.yaml`：

```yaml
federation:
  enabled: true
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"        # 容器内端口
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"      # 子集群 NodePort
      description: "子集群 24"
      enabled: true
```

子集群：`federation.enabled: false`

---

## 二、API 使用

### 端点总览

| 端点 | 说明 |
|------|------|
| `/ask` | 单集群查询（主入口） |
| `/federation/ask` | 多集群并发查询（v1） |
| `/federation/ask/v2` | Agent-to-Agent 智能路由（v2） |
| `/health` | 健康检查 |
| `/tools` | 工具列表 |
| `/runbooks` | Runbook 列表 |
| `/reports` | 诊断报告列表 |

### `/ask` 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | **必填** | 问题内容 |
| `stream` | bool | `true` | 是否流式输出 |
| `format` | string | `"text"` | 输出格式：`text` / `sse` |
| `max_steps` | int | `20` | LLM 最大工具调用轮数（1-100） |

### `/federation/ask` 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | **必填** | 问题内容 |
| `max_steps` | int | `30` | 每个子集群最大步数 |
| `conclusion_max_tokens` | int | `8192` | 子集群结论 token 上限（0=不限） |

### `/federation/ask/v2` 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | **必填** | 问题内容 |
| `max_steps` | int | `30` | Agent 最大步数 |

### 使用示例

```bash
# 单集群：故障诊断
curl -G "http://HOST:30800/ask" --data-urlencode "q=Pod 为什么一直重启"

# 单集群：数据查询（减少步数加速）
curl -G "http://HOST:30800/ask" --data-urlencode "q=集群 CPU 使用率" --data-urlencode "max_steps=10"

# 单集群：非流式
curl -G "http://HOST:30800/ask" --data-urlencode "q=Pod列表" --data-urlencode "stream=false"

# 联邦 v1：查询所有集群
curl -G "http://HOST:30800/federation/ask" --data-urlencode "q=哪个集群 CPU 最高"

# A2A v2：智能路由到指定集群
curl -G "http://HOST:30800/federation/ask/v2" --data-urlencode "q=查询 cluster-24 的内存"

# A2A v2：对比多个集群
curl -G "http://HOST:30800/federation/ask/v2" --data-urlencode "q=对比 main 和 cluster-24 的 CPU"

# A2A v2：不同集群不同问题
curl -G "http://HOST:30800/federation/ask/v2" --data-urlencode "q=查询 main 的内存和 cluster-24 的 CPU"
```

---

## 三、常见问题

**Q: `max_steps` 设多少合适？**
简单数据查询 `10-15`，复杂诊断 `20-30`，默认 20 适合大多数场景。

**Q: 主集群 URL 用什么？**
必须用 `http://localhost:8000`（容器内端口），不能用 NodePort 30800。

**Q: A2A 和并发模式的区别？**
并发模式查询所有集群，A2A 由 LLM 智能决定查询哪些。

**Q: 如何禁用子集群？**
`federation.sub_agents` 中设置 `enabled: false`，重新部署。
