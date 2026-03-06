# 多集群联邦查询部署与使用指南

## 概述

联邦查询功能允许主集群（云管平台）并发调用多个子集群的 AIOps Agent，汇总各子集群的诊断报告后由 LLM 合成统一的多集群分析结论。

**核心特性**：
- 子集群代码零改动，仅需 NodePort 可达
- 主集群并发查询，自动 Token 压缩
- LLM 智能合成多集群对比报告
- 原有单集群 `/ask` 端点完全不受影响

---

## 架构说明

```
用户 → 主集群 /federation/ask
         ↓ asyncio.gather（并发）
    ┌────┴────────────┐
    ↓                  ↓
子集群A /ask         子集群B /ask
(完整单集群诊断)    (完整单集群诊断)
    ↓                  ↓
    └────┬────────────┘
         ↓ 汇总到内存
    [Token 估算 + 压缩]
         ↓
    LLM synthesis（流式输出）
         ↓
    多集群统一汇总报告
```

---

## 部署步骤

### 1. 子集群（无需任何改动）

子集群保持现有部署，确保：
- aiops-copilot 服务正常运行
- NodePort 30800 可从主集群访问
- 配置中 `federation.enabled: false` 或省略 `federation` 块

**验证子集群可达**：
```bash
# 在主集群节点上测试
curl -X POST "http://10.2.0.24:30800/ask" \
  -d "q=集群健康状态" \
  -d "stream=false" \
  -d "max_steps=5"
```

### 2. 主集群配置

编辑 `deploy/configmap/config.yaml`，启用联邦并配置子集群列表：

```yaml
federation:
  enabled: true                    # 主集群开启
  max_tokens_per_agent: 12000      # 单个子集群报告超过此 token 数则压缩
  synthesis_timeout: 300           # 等待子集群响应的最大秒数（5分钟）
  sub_agents:
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"
      description: "被管集群 10.2.0.24"
      enabled: true
    - name: "cluster-25"
      url: "http://10.2.0.25:30800"
      description: "被管集群 10.2.0.25"
      enabled: true
```

### 3. 重新部署主集群

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta

# 构建新镜像
make build

# 推送到镜像仓库
make push

# 部署到 K8s（会自动滚动更新）
make deploy

# 查看部署状态
kubectl rollout status deployment/aiops-copilot -n aiops

# 查看日志确认联邦初始化
kubectl logs -f deployment/aiops-copilot -n aiops | grep FEDERATION
```

**预期日志**：
```
[FEDERATION] 注册表加载完成，共 2 个子集群
[FEDERATION] FederationCoordinator 初始化完成
```

---

## 使用方式

### 联邦查询端点

**GET 方式**（推荐）：
```bash
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=哪个集群的CPU利用率最高？请对比分析"
```

**POST 方式**：
```bash
curl -X POST "http://10.2.0.48:30800/federation/ask" \
  -d "q=所有集群中有哪些异常Pod？请汇总" \
  -d "max_steps=30"
```

### 单集群查询（原有功能不变）

```bash
# 查询主集群自身
curl -X POST "http://10.2.0.48:30800/ask" \
  -d "q=本集群健康状态"
```

---

## 输出示例

联邦查询会返回结构化的多集群对比报告：

```markdown
🌐 联邦查询：共查询 2 个子集群，2 个成功响应

## 多集群统一诊断报告

### 1. 各集群问题概览对比表

| 集群名称 | 主要问题 | 严重程度 | 状态 |
| :--- | :--- | :--- | :--- |
| cluster-24 | Pod CrashLoopBackOff (3个) | 高 | 需立即处理 |
| cluster-25 | 节点资源不足 | 中 | 监控中 |

### 2. 共性问题
- **内存压力**：两个集群均存在节点内存使用率超过 80% 的情况

### 3. 差异化问题
- **cluster-24 特有**：应用容器持续崩溃，需检查日志
- **cluster-25 特有**：磁盘 I/O 瓶颈，需扩容存储

### 4. 跨集群优先级排序
1. cluster-24 的 CrashLoopBackOff 问题（最高优先级）
2. 两集群的内存压力问题
3. cluster-25 的磁盘 I/O 问题

### 5. 分集群修复建议

#### 集群：cluster-24
1. 检查 Pod 日志：`kubectl logs <pod> --previous`
2. 检查资源限制和配置
...

#### 集群：cluster-25
1. 扩容节点或调整 Pod 资源请求
2. 监控磁盘 I/O 指标
...
```

---

## 故障排查

### 问题1：联邦端点返回"未启用"

**现象**：
```
❌ 联邦查询未启用。
请在主集群 config.yaml 中设置 federation.enabled: true
```

**解决**：
1. 确认 `deploy/configmap/config.yaml` 中 `federation.enabled: true`
2. 重新部署：`make deploy`
3. 检查日志：`kubectl logs -f deployment/aiops-copilot -n aiops | grep FEDERATION`

### 问题2：子集群查询失败

**现象**：
```
⚠️ 以下 1 个子集群查询失败，已从合成中排除：
- cluster-24 (http://10.2.0.24:30800): 请求超时（300s）
```

**排查步骤**：
1. **网络连通性**：
   ```bash
   # 在主集群 Pod 内测试
   kubectl exec -it deployment/aiops-copilot -n aiops -- \
     curl -s http://10.2.0.24:30800/health
   ```

2. **子集群服务状态**：
   ```bash
   # 在子集群上检查
   kubectl get svc -n aiops
   kubectl get pods -n aiops
   ```

3. **超时调整**：如果子集群响应慢，增加 `synthesis_timeout`：
   ```yaml
   federation:
     synthesis_timeout: 600  # 改为 10 分钟
   ```

### 问题3：LLM 合成失败

**现象**：
```
❌ LLM 合成失败: API key not found
```

**解决**：
1. 确认环境变量：
   ```bash
   kubectl get secret aiops-secrets -n aiops -o yaml
   ```
2. 检查 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 是否正确配置

---

## 性能调优

### Token 压缩阈值

默认单个子集群报告超过 12000 tokens 会触发压缩。调整方法：

```yaml
federation:
  max_tokens_per_agent: 15000  # 增大阈值，减少压缩频率
```

### 并发超时

默认等待子集群响应最多 300 秒（5分钟）。对于大规模集群：

```yaml
federation:
  synthesis_timeout: 600  # 增加到 10 分钟
```

### 子集群 max_steps

联邦查询时，每个子集群的 `max_steps` 默认为 30。可通过 API 参数调整：

```bash
curl -X POST "http://10.2.0.48:30800/federation/ask" \
  -d "q=问题" \
  -d "max_steps=50"  # 增加子集群诊断深度
```

---

## 安全建议

1. **网络隔离**：子集群 NodePort 仅对主集群开放，使用防火墙规则限制
2. **认证机制**：生产环境建议在主子集群间增加 API Token 认证（需自行扩展）
3. **日志审计**：所有联邦查询请求都会记录 `[FEDERATION]` 前缀日志

---

## 测试验证

### 本地测试脚本

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta

# 运行真实集成测试（用本机服务模拟子集群）
TEST_SUB_CLUSTER_URL="http://10.2.0.48:30800" \
TEST_MAX_STEPS=5 \
TEST_QUESTION="集群当前有哪些异常Pod" \
.venv/bin/python test/test_federation_real.py
```

### 生产验证

```bash
# 1. 健康检查
curl http://10.2.0.48:30800/health

# 2. 单集群查询（验证原功能不受影响）
curl -X POST "http://10.2.0.48:30800/ask" -d "q=集群状态"

# 3. 联邦查询（验证新功能）
curl -X POST "http://10.2.0.48:30800/federation/ask" \
  -d "q=所有集群的资源使用情况对比"
```

---

## 常见问题

**Q: 联邦查询会影响单集群 `/ask` 端点吗？**
A: 不会。两个端点完全独立，`/ask` 保持原有行为。

**Q: 子集群需要升级代码吗？**
A: 不需要。子集群保持现有版本，仅主集群需要升级。

**Q: 可以动态添加/删除子集群吗？**
A: 可以。修改 ConfigMap 后执行 `kubectl rollout restart deployment/aiops-copilot -n aiops` 即可。

**Q: 联邦查询的成本如何？**
A: 主要成本是 LLM 合成调用（1次）+ 子集群数量 × 单集群诊断成本。Token 压缩机制可降低 LLM 输入成本。

---

## 技术细节

### 模块结构

```
robusta/app/core/federation/
├── __init__.py         # FederationCoordinator 入口
├── registry.py         # 子集群配置加载
├── client.py           # 异步 HTTP 客户端
└── aggregator.py       # 并发聚合 + LLM 合成
```

### 关键设计

1. **并发查询**：使用 `asyncio.gather` 并发调用所有子集群，最大化效率
2. **Token 压缩**：超过阈值的报告通过 LLM 压缩为摘要，保留关键信息
3. **流式输出**：合成过程实时流式返回，用户体验友好
4. **事件循环隔离**：使用 `ThreadPoolExecutor` 运行 asyncio，避免与 FastAPI 事件循环冲突

### 日志前缀

所有联邦相关日志使用 `[FEDERATION]` 前缀，便于过滤：

```bash
kubectl logs -f deployment/aiops-copilot -n aiops | grep FEDERATION
```

---

## 版本历史

- **v1.0.0** (2026-03-05): 初始版本，支持多集群并发查询和 LLM 合成
