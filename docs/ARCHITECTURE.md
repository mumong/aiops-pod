# 架构说明

本文只描述当前正式实现。

## 1. 当前正式架构

当前服务对外是一个 FastAPI API Server，内部核心是：

- AICall(LangGraph) 工作流执行
- MCP 工具调用
- Runbook 知识库
- 多集群 federation

当前正式 API 已经明确分流：

- `/ask`：诊断工作流
- `/query`：查询工作流

## 2. 组件分层

### API 层

- [app/api/routes.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/api/routes.py)
- 对外暴露 `/ask`、`/query`、`/federation/*`、`/health`、`/tools`、`/runbooks`、`/reports`

职责：

- 参数解析
- 路由到对应工作流
- 选择流式或同步响应

### 服务编排层

- [app/core/service.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/service.py)

职责：

- 初始化配置、模型、工具、runbook、联邦组件
- 执行单集群查询与工作流
- 输出统一文本流

### 工作流层

- [app/core/workflow/graph.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/graph.py)
- [app/core/workflow/executor.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/executor.py)
- [app/core/workflow/nodes/](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/nodes)

职责：

- 定义图结构
- 在节点间传递 `WorkflowState`
- 汇总 metrics 与报告

### 知识与提示词层

- [app/core/prompts.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/prompts.py)
- [deploy/configmap/runbooks.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/runbooks.yaml)

职责：

- 定义节点 prompt
- 提供 runbook catalog 与 runbook 内容

### 工具层

- `mcp_servers` 配置定义实际工具入口
- 运行时通过 MCP SSE 调用外部能力

当前典型工具：

- Kubernetes
- Prometheus
- Bash
- Helm
- Runbook

### 联邦层

- [app/core/federation/](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/federation)

职责：

- 子集群注册
- 广播查询
- Agent-to-Agent 智能路由
- 聚合结果

## 3. 单集群正式链路

### `/ask`

```text
用户问题
  -> layer
  -> evidence
  -> rca
  -> conclusion
  -> 最终诊断报告
```

#### layer

- 判定 `HEALTHY / L0 / L1 / L2 / L3 / L4`
- 提取关键实体
- 提取可能场景

#### evidence

- 制定证据采集计划
- 调用工具采集真实数据
- 计算证据完整度

#### rca

- 做根因推理
- 产出 `primary_runbooks`
- 产出根因、因果链、限制项

#### conclusion

- 汇总前三个节点输出
- 生成最终报告

### `/query`

```text
用户问题
  -> layer
  -> conclusion
  -> 最终查询结果
```

关键点：

- `layer` 在 direct query 模式下不仅做分类，也负责真实工具采集
- `layer` 直接生成结构化 `query_result`
- `conclusion` 主要做渲染，不再重复做完整诊断

## 4. 为什么 ask 和 query 要分开

这是当前架构最重要的设计之一。

### `/ask`

适合：

- 我的集群有什么问题
- 为什么这个 Pod 一直重启
- 帮我分析一下当前异常

特点：

- 更慢
- 更深
- 会走证据采集和根因分析

### `/query`

适合：

- CPU / 内存 / 磁盘 / 网络是多少
- 某个列表、某个状态、某个指标

特点：

- 更快
- 更窄
- 不走 evidence / rca

## 5. 状态流转

LangGraph 原生负责状态流转，但不会自动帮你做“对下一个节点最合适的信息整理”。

所以当前实现分两层：

1. `WorkflowState`
   负责节点间传字段
2. 节点代码
   负责把上游结果重新组织成下游更容易理解的输入

典型字段：

- `layer`
- `layer_analysis`
- `layer_full_analysis`
- `evidence_analysis`
- `evidence_items`
- `rca_analysis`
- `primary_runbook_id`
- `query_result`

## 6. Runbook 机制

### 使用

- runbook catalog 会注入到节点 prompt 中
- 模型可调用 `fetch_runbook`
- 允许抓取多个 runbook

### 展示

最终报告中的：

- `核心 Runbook`
- `参考 Runbook`

都由 [app/core/workflow/reporter.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/reporter.py) 从实际执行痕迹中归一化得到。

规则：

- `核心 Runbook`
  只认 AI 明确声明的 `primary_runbooks`
- `参考 Runbook`
  展示所有实际使用过且在 catalog 中存在的 runbook

## 7. 联邦架构

### 广播模式

- `/federation/ask`
- `/federation/query`

特点：

- 对所有子集群发相同问题
- 聚合更直接

### Agent 模式

- `/federation/ask/v2`
- `/federation/query/v2`

特点：

- 先理解用户意图
- 再决定查哪些集群
- 支持不同集群不同问题

## 8. 当前文档边界

如果你只需要快速掌握：

1. 先看 [README.md](/root/huhu/agent/combine-aiops-mcp/robusta/README.md)
2. 再看 [docs/GUIDE.md](/root/huhu/agent/combine-aiops-mcp/robusta/docs/GUIDE.md)
3. API 细节看 [docs/接口设计与实现.md](/root/huhu/agent/combine-aiops-mcp/robusta/docs/%E6%8E%A5%E5%8F%A3%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%AE%9E%E7%8E%B0.md)
