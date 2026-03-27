# L1 Kubelet 通信故障 - Node NotReady 诊断手册
# 场景：节点被标记为不可调度 (NoSchedule taint)，AI Agent 通过 kubectl get nodes 直接看到异常

---

## 场景识别特征

| 类别 | 关键词 | 典型表现 |
|------|--------|----------|
| Taint 标签 | aiops-test-scenario=l1-node-issue | 故障注入标记 |
| 节点状态 | NotReady, Unknown, NoSchedule | kubectl get nodes 显示节点异常 |
| 调度状态 | Unschedulable | 节点标记为不可调度 |

---

## 1. 诊断步骤

### 1.1 检查节点状态

```bash
kubectl get nodes -o wide
```

**预期结果**：
- `STATUS` 列显示 `NotReady` 或 `Unknown`
- `ROLES` 列显示节点角色
- `VERSION` 列显示 kubelet 版本

---

### 1.2 检查节点条件

```bash
kubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type=="Ready")]}'
```

**预期结果**：
- `status` 字段为 `False`
- `reason` 可能显示 `NodeTaintUnschedulable`
- `message` 显示具体原因

---

### 1.3 检查节点 Taint

```bash
kubectl describe node <node-name>
```

**预期结果**：
- `Taints` 部分显示 taint 信息

---

## 2. 排查步骤

### 2.1 检查 kubelet 日志

```bash
journalctl -u kubelet --since "60 min ago" | tail -100
```

**关注信息**：
- x509 证书错误
- TLS 握手失败
- API Server 连接失败

---

### 2.2 检查节点事件

```bash
kubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'
```

**关注信息**：
- NodeReady 状态变化事件
- Taint 相关事件
- FailedMount, PLEG unhealthy 相关事件

---

## 3. 证据链

| 步骤 | 命令/工具 | 原始数据 | 分析结论 |
|-------|------------|----------|-----------|
| 1 | kubectl get nodes | STATUS=NotReady, Taints 存在 | 节点被标记为不可用 |
| 2 | kubectl get node ...jsonpath | status=False | Ready 条件未满足 |
| 3 | kubectl describe node | Taints 包含故障标记 | 存在故障注入 |
| 4 | kubectl get events | NodeNotReady 相关事件 | 集群记录节点异常 |

---

## 4. 根因分析

### 4.1 层级判定

**层级**: L1 - 集群与节点层

**判定理由**：
- 异常发生在节点级别（Node NotReady）
- Taint 标记导致调度器不再调度 Pod
- 这是典型的 **L1 层节点问题**
- 你需要进行对比验证。得到结论的时候要利用 工具命令来验证对比，二次确认！ -

---

### 4.2 可能原因

| 可能性 | 原因 | 置信度 | 说明 |
|---------|------|--------|------|
| 高 | Taint 导致节点被标记为不可调度 | 90% | 预期的故障注入 |
| 中 | kubelet 证书问题 | 70% | 需要检查证书有效性 |
| 低 | 网络分区 | 50% | 可能导致 API Server 不可达 |

---

## 5. 快速命令参考

```bash
# 诊断
alias diag-node='kubectl get nodes && kubectl describe node && kubectl get events -A --field-selector involvedObject.kind=Node'

# 快速检查 Ready 节点
kubectl get nodes --no-headers | grep Ready | grep -v NotReady

# 检查特定节点的所有条件
kubectl get node <node-name> -o jsonpath='{.status.conditions[*]}'

# 清理 taint
kubectl taint nodes <node-name> <taint-key>-

# 查看 kubelet 日志
journalctl -u kubelet --tail=50
```
