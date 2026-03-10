# 快速开始

---

## 一、LLM 配置

修改 `deploy/secrets/core.yaml`，填入 LLM API Key：

```yaml
stringData:
  LLM_API_KEY: "sk-xxx"
  LLM_MODEL: "deepseek/deepseek-chat"     # 或 anthropic/claude-sonnet-4-6 等
  LLM_API_BASE: ""                          # DeepSeek 留空，Claude 需填代理地址
  USE_WORKFLOW: "true"                      # 启用工作流模式（推荐）
```

详细 LLM 配置方式见 [配置指南](CONFIGURATION.md)。

---

## 二、部署

### 主集群（启用联邦查询）

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make build push deploy-master
```

### 子集群（关闭联邦查询）

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make build push deploy-slave
```

### 常用运维命令

```bash
make logs        # 查看日志
make restart     # 重启服务
make delete      # 删除部署（保留 namespace）
```

### 验证部署

```bash
curl http://10.2.0.48:30800/health    # 主集群
curl http://10.2.0.24:30800/health    # 子集群
```

---

## 三、联邦查询配置

### 主集群

在 `deploy/configmap/config.yaml` 中配置：

```yaml
federation:
  enabled: true
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"        # 容器内端口，不能用 NodePort
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"      # 子集群 NodePort
      description: "子集群 24"
      enabled: true
```

### 子集群

```yaml
federation:
  enabled: false
```

**注意**：主集群 URL 必须用 `http://localhost:8000`，不能用 `http://localhost:30800`。

---

## 四、使用方式

### 单集群查询

```bash
# 故障诊断
curl -G "http://HOST:30800/ask" \
  --data-urlencode "q=payment-service 的 Pod 为什么一直重启"

# 数据查询
curl -G "http://HOST:30800/ask" \
  --data-urlencode "q=集群 CPU 使用率"

# 自定义最大步数
curl -G "http://HOST:30800/ask" \
  --data-urlencode "q=Pod列表" \
  --data-urlencode "max_steps=10"

# 非流式输出
curl -G "http://HOST:30800/ask" \
  --data-urlencode "q=集群状态" \
  --data-urlencode "stream=false"

# SSE 格式输出
curl -G "http://HOST:30800/ask" \
  --data-urlencode "q=Pod状态" \
  --data-urlencode "format=sse"
```

### 联邦查询 — 并发模式（v1）

查询所有配置的集群：

```bash
curl -G "http://HOST:30800/federation/ask" \
  --data-urlencode "q=哪个集群 CPU 最高" \
  --data-urlencode "max_steps=30" \
  --data-urlencode "conclusion_max_tokens=8192"
```

### Agent-to-Agent — 智能路由（v2）

```bash
# 查询指定集群
curl -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=查询 cluster-24 的 CPU"

# 查询主集群
curl -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=主集群的内存使用情况"

# 对比多个集群
curl -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU"

# 查询所有集群
curl -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=所有集群的状态"

# 不同集群不同问题
curl -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=查询 main 的内存和 cluster-24 的 CPU"
```

---

## 五、API 参数参考

### `/ask`

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `q` | string | **必填** | — | 问题内容 |
| `stream` | bool | `true` | — | 是否流式输出 |
| `format` | string | `"text"` | text / sse | 输出格式 |
| `max_steps` | int | `20` | 1-100 | LLM 最大工具调用轮数 |

### `/federation/ask`

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `q` | string | **必填** | — | 问题内容 |
| `max_steps` | int | `30` | 1-100 | 每个子集群最大步数 |
| `conclusion_max_tokens` | int | `8192` | ≥0 | 子集群结论 token 上限（0=不限） |

### `/federation/ask/v2`

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `q` | string | **必填** | — | 问题内容 |
| `max_steps` | int | `30` | 1-100 | Agent 最大步数 |

---

## 六、端点总览

| 端点 | 说明 | 适用场景 |
|------|------|----------|
| `/ask` | 单集群查询 | 查询当前集群的数据或诊断故障 |
| `/federation/ask` | 并发查询所有集群 | 全局对比、汇总 |
| `/federation/ask/v2` | 智能路由查询 | 选择性查询指定集群、复杂跨集群问题 |
| `/health` | 健康检查 | 监控 |
| `/tools` | 工具列表 | 查看可用工具 |
| `/runbooks` | Runbook 列表 | 查看知识库 |
| `/reports` | 报告列表 | 查看历史诊断报告 |

---

## 七、常见问题

**Q: `max_steps` 设多少合适？**

A: 简单数据查询设 `10-15`，复杂诊断设 `20-30`。默认 20 适合大多数场景。

**Q: 为什么要配置主集群本身？**

A: 当用户问"所有集群"时，应包括主集群。配置后主集群与子集群地位平等。

**Q: Agent-to-Agent 和并发模式有什么区别？**

A:
- 并发模式（v1）：查询所有配置的集群，适合全局对比
- Agent-to-Agent（v2）：LLM 智能决定查询哪些集群，适合选择性查询

**Q: 如何临时禁用某个子集群？**

A: 在 `federation.sub_agents` 中设置 `enabled: false`，重新部署。

---

**详细配置**：[配置指南](CONFIGURATION.md) | **架构说明**：[架构设计](ARCHITECTURE.md) | **提示词**：[提示词参考](PROMPTS.md)
