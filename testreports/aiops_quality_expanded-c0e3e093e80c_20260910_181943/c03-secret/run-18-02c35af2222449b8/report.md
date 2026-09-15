## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod定义中引用了不存在的Secret 'unavailable-input' 且未标记为Optional，导致Kubelet挂载Volume失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`：`MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` (fact-fea57ba12555) | 直接定位 Volume 挂载失败的根因为 Secret 资源缺失 |
| 2 | K8s State | kubernetes | `ContainerCreating`；Phase 为 `Pending`；Condition 显示 `ContainersNotReady` (fact-955667756fc6, fact-1c1f166fc911, fact-3ae7d5ef47b6) | 确认 Pod 始终处于初始化阶段，容器未能启动 |
| 3 | K8s State | kubernetes | `restart_count: 0` (fact-085914a5caa5) | 排除应用内部崩溃或 OOM 等运行时故障 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 中 `ContainerCreating` 值为 1 (fact-b25c9c35a571) | 独立印证 K8s 事件指出的容器挂载等待状态 |
| 5 | K8s State | kubernetes | 资源请求/限制配置确认（如 `cpu: 5m`, `memory: 8Mi`) (fact-027b7798a0bf, fact-0e18b2ad28d9) | 排除资源不足（OOMKilled 或 CPU Throttling）导致的异常 |

证据 1 (事件) 直接指出了失败对象与缺失资源的关联；证据 2 (状态) 与证据 4 (指标) 在现象层面互相印证，说明故障发生在启动前的挂载阶段且持续发生；证据 3 排除了运行时的崩溃可能，进一步确证了故障的根源在于资源准备（挂载）阶段。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码或定义错误引用了不存在的 Secret 'unavailable-input' → Kubelet 在挂载 'input' Volume 时发现资源缺失 (FailedMount) → Pod 卡在 ContainerCreating 状态 → 用户无法访问该应用
```

### 根因结论

**已确认根因**：Pod 的 Volume 定义中引用了 Secret 名称 `unavailable-input`，但该资源在当前命名空间中不存在，且未被标记为 `Optional`，导致挂载逻辑失败 (fact-fea57ba12555)。

现有 K8s 事件日志（fact-fea57ba12555）直接描述了“secret not found”这一事实，结合状态（fact-1c1f166fc911）与指标（fact-b25c9c35a571）对挂载失败状态的交叉印证，因果链已闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.3s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-v04/workload: 36.1s (Evidence 31.1s, RCA 4.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
