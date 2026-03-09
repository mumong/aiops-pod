# Agent-to-Agent 快速开始

## 一、配置文件修改

### 主集群配置

**文件位置**：`deploy/configmap/config.yaml`

```yaml
federation:
  enabled: true  # 主集群设为 true
  sub_agents:
    # 主集群本身（重要：让主集群也可被查询）
    - name: "main"
      url: "http://localhost:30800"
      description: "主集群"
      enabled: true

    # 子集群列表
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"
      description: "子集群 24"
      enabled: true

    - name: "cluster-48"
      url: "http://10.2.0.48:30800"
      description: "子集群 48"
      enabled: true
```

**关键点**：
- `federation.enabled: true`
- 必须包含主集群本身（name: "main", url: "http://localhost:30800"）
- 添加所有子集群

### 子集群配置

**文件位置**：`deploy/configmap/config.yaml`

```yaml
federation:
  enabled: false  # 子集群设为 false
```

子集群只需要关闭 federation 即可。

## 二、部署

### 主集群部署

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make master
```

### 子集群部署

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make slave
```

### 验证部署

```bash
# 检查主集群
curl http://10.2.0.48:30800/health

# 检查子集群
curl http://10.2.0.24:30800/health
```

## 三、使用方式

### 1. 单集群查询

```bash
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=集群状态"
```

### 2. 联邦查询（并发模式）

查询所有配置的集群：

```bash
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=哪个集群CPU最高"
```

### 3. Agent-to-Agent（智能路由）

**查询指定集群**：
```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=查询 cluster-24 的 CPU"
```

**查询主集群**：
```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=主集群的内存使用情况"
```

**对比多个集群**：
```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU"
```

**查询所有集群（包括主集群）**：
```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=所有集群的状态"
```

**不同集群不同问题**：
```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=查询 main 的内存和 cluster-24 的 CPU"
```

## 四、端点说明

| 端点 | 说明 | 适用场景 |
|------|------|----------|
| `/ask` | 单集群查询 | 查询单个集群 |
| `/federation/ask` | 并发查询所有集群 | 全局对比 |
| `/federation/ask/v2` | 智能路由查询 | 选择性查询、复杂问题 |

## 五、常见问题

**Q: 为什么要配置主集群本身？**

A: 当用户问"所有集群"时，应该包括主集群。配置后主集群与子集群地位平等。

**Q: 主集群的 URL 用什么？**

A: 使用 `http://localhost:30800` 或 `http://127.0.0.1:30800`

**Q: 如何禁用某个子集群？**

A: 设置 `enabled: false`

**Q: Agent-to-Agent 和并发模式有什么区别？**

A:
- 并发模式：查询所有配置的集群
- Agent-to-Agent：LLM 智能决定查询哪些集群

## 六、故障排查

**问题：主集群无法访问子集群**

```bash
# 测试网络连通性
curl http://10.2.0.24:30800/health
```

**问题：主集群查询自己失败**

检查配置文件是否包含主集群：
```yaml
sub_agents:
  - name: "main"
    url: "http://localhost:30800"
    enabled: true
```

## 七、提示词管理

所有提示词统一管理在：`app/core/prompts.py`

修改 `FEDERATION_AGENT_PROMPT` 后需要重新部署：
```bash
make master
```

---

**更多技术细节**：参考 `A2A_TECHNICAL_DESIGN.md`
