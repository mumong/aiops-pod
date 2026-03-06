# 联邦查询（多集群 Agent-to-Agent）完整指南

生成时间：2026-03-06

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [架构原理](#架构原理)
4. [配置说明](#配置说明)
5. [部署指南](#部署指南)
6. [使用示例](#使用示例)
7. [故障排查](#故障排查)

---

## 概述

### 什么是联邦查询？

联邦查询（Federation Query）是一种多集群诊断能力，允许主集群（云管平台）并发调用多个子集群的 AIOps Agent，汇总各子集群的诊断报告，经 LLM 合成后输出统一的多集群报告。

### 核心特性

- ✅ **子集群零改动**：子集群无需升级代码，仅需 NodePort 30800 可达
- ✅ **并发高效**：asyncio.gather 并发查询，减少总耗时
- ✅ **智能压缩**：Token 估算与 LLM 压缩，避免超长输入
- ✅ **流式输出**：实时返回合成进度，用户体验友好
- ✅ **完全向后兼容**：原有 `/ask` 端点不受影响

### 架构总览

```
用户 → 主集群 /federation/ask
         ↓
    并发查询（asyncio.gather）
         ↓
    ┌────┴────────────┐
    ↓                  ↓
子集群A /ask         子集群B /ask
(完整单集群诊断)    (完整单集群诊断)
    ↓                  ↓
    └────┬────────────┘
         ↓ 收集到内存
    Token 估算 + 压缩
         ↓
    LLM 合成（流式输出）
         ↓
    多集群统一报告
```

---

## 快速开始

### 前置条件

1. 主集群和子集群都已部署 aiops-copilot
2. 主集群能访问子集群的 NodePort 30800
3. 网络连通性已验证

### 3 步部署

#### 步骤 1：配置主集群

编辑 `deploy/configmap/config.yaml`：

```yaml
federation:
  enabled: true  # 改为 true
  max_tokens_per_agent: 22000  # 单个子集群报告 token 上限（0=不限制）
  synthesis_timeout: 300       # 等待子集群响应的最大秒数
  sub_agents:
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"
      description: "被管集群 10.2.0.24"
      enabled: true
```

#### 步骤 2：部署主集群

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make build push deploy
```

#### 步骤 3：验证

```bash
# 健康检查
curl http://10.2.0.48:30800/health

# 联邦查询
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=哪个集群CPU最高"
```

---

## 架构原理

### 核心组件

#### 1. FederationCoordinator（协调器）

- 全局单例，管理联邦查询生命周期
- 从配置加载 AgentRegistry
- 提供统一的 `query()` 入口

#### 2. AgentRegistry（注册表）

- 从 YAML 配置加载子集群列表
- 支持热重载（检测配置文件 mtime）
- 过滤已启用的子集群

#### 3. SubAgentClient（HTTP 客户端）

- 异步调用子集群的 `/ask` 端点
- 超时控制和错误处理
- 使用 `stream=false` 获取完整响应

#### 4. FederationAggregator（聚合器）

- 并发查询所有子集群
- Token 估算与压缩
- LLM 合成多集群报告

### 数据流转

**内存存储机制**：
- 子集群响应存储在 `SubAgentResult.text` 字段
- 所有结果存储在 `List[SubAgentResult]` 中
- 完全内存处理，无持久化
- Token 估算（len/3），超过阈值自动 LLM 压缩

**网络传输**：
- 协议：标准 HTTP POST
- 格式：纯文本（Markdown）
- 编码：UTF-8
- 大小：通常 5-50 KB/子集群

### 单集群与多集群的关系

**关键设计**：
- 每个子集群都走完整的单集群 `/ask` 逻辑
- 子集群使用 `SYSTEM_PROMPT` 或 `WORKFLOW_PROMPTS`
- 主集群使用独立的 `FEDERATION_SYNTHESIS_PROMPT` 合成
- 子集群不知道自己被"联邦查询"

---

## 配置说明

### 主集群配置

**文件位置**：`deploy/configmap/config.yaml`

```yaml
federation:
  enabled: true                    # 主集群设为 true
  max_tokens_per_agent: 22000      # Token 上限（0=不限制）
  synthesis_timeout: 300           # 超时时间（秒）
  sub_agents:
    - name: "cluster-24"           # 子集群名称
      url: "http://10.2.0.24:30800"  # 子集群 URL
      description: "被管集群"       # 描述
      enabled: true                # 是否启用
```

### 子集群配置

**无需任何配置**，或者设置：

```yaml
federation:
  enabled: false  # 子集群设为 false 或省略
```

### 参数说明

| 参数 | 说明 | 默认值 | 建议值 |
|------|------|--------|--------|
| `enabled` | 是否启用联邦查询 | false | 主集群 true，子集群 false |
| `max_tokens_per_agent` | 单个子集群报告 token 上限 | 12000 | 22000（0=不限制） |
| `synthesis_timeout` | 等待子集群响应的最大秒数 | 300 | 300-600 |

---

## 部署指南

### 使用 Makefile 部署

#### 主集群部署

```bash
make master  # 自动配置 federation.enabled=true
```

#### 子集群部署

```bash
make slave   # 自动配置 federation.enabled=false
```

#### 通用部署

```bash
make build push deploy  # 使用当前配置
```

### 手动部署

1. 编辑配置文件
2. 构建镜像：`make build`
3. 推送镜像：`make push`
4. 部署到 K8s：`make deploy`

### 验证部署

```bash
# 检查 Pod 状态
kubectl get pods -n aiops

# 查看日志
kubectl logs -f deployment/aiops-copilot -n aiops | grep FEDERATION

# 健康检查
curl http://10.2.0.48:30800/health
```

---

## 使用示例

### 对比分析

```bash
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=哪个集群的CPU利用率最高？请对比分析"
```

### 全局诊断

```bash
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=我的集群有什么问题？"
```

### 指定参数

```bash
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=集群状态" \
  --data-urlencode "max_steps=30" \
  --data-urlencode "conclusion_max_tokens=8192"
```

### 输出格式

多集群报告包含：
- 📊 多集群诊断概览
- 🌐 各集群状态对比表
- 🕵️ 跨集群证据汇总
- 🎯 问题分析（共性问题 + 差异化问题）
- 📋 跨集群优先级排序
- 🛠️ 分集群修复建议

---

## 故障排查

### 常见问题

#### 1. 子集群查询失败

**现象**：
```
⚠️ 以下 1 个子集群查询失败：
- `cluster-24` (http://10.2.0.24:30800): Connection timeout
```

**排查**：
```bash
# 检查网络连通性
curl -v http://10.2.0.24:30800/health

# 检查子集群 Pod 状态
kubectl get pods -n aiops

# 检查子集群日志
kubectl logs -f deployment/aiops-copilot -n aiops
```

#### 2. Token 超限

**现象**：日志显示 "报告超出阈值，开始压缩"

**解决**：
- 增加 `max_tokens_per_agent` 值
- 或设置为 0 不限制（会自动处理模型上下文限制）

#### 3. 合成失败

**现象**：
```
❌ LLM 合成失败: API key invalid
```

**排查**：
```bash
# 检查环境变量
kubectl get secret aiops-secret -n aiops -o yaml

# 检查 API key 是否有效
```

### 调试日志

启用详细日志：

```bash
# 查看联邦查询日志
kubectl logs -f deployment/aiops-copilot -n aiops | grep "\[FEDERATION\]"
```

日志示例：
```
[FEDERATION] 开始并发查询 1 个子集群，问题: 哪个集群CPU最高...
[FEDERATION] cluster-24 响应成功, 长度: 5432 chars, 耗时: 40.4s
[FEDERATION] 开始 LLM 合成, 总输入 tokens 约: 1810
```

---

## 附录

### 性能数据

- 单个子集群响应时间：~40 秒
- 主集群合成时间：~45 秒
- 总耗时：~85 秒（1 个子集群）
- 网络传输：< 1 秒（局域网）

### 子集群报告存储

子集群的详细报告会自动保存到：
- 目录：`reports/`
- 格式：`{cluster_name}_{timestamp}.md`
- 示例：`cluster-24_20260306_135030.md`

查看保存的报告：
```bash
ls -lh reports/
cat reports/cluster-24_20260306_135030.md
```

### 相关文档

- 整体架构：`ARCHITECTURE.md`
- 项目入口：`README.md`
