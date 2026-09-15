## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod `aiops-case-v04/workload` 处于 `ContainerCreating` (Waiting) 状态，未分配 IP。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v04/workload` 状态：`Pending` | 确认 Pod 未正常启动 |
| 2 | K8s Event | kubernetes | Warning `FailedMount`: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接指出挂载卷失败的根本原因 |
| 3 | K8s Config | kubernetes | Volume 引用 Secret: `unavailable-input` | 提供触发故障的具体资源引用 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值: `1` (reason: `ContainerCreating`) | 量化容器阻塞状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值: `0` | 证实应用尚未启动过 |

**证据印证：**
*   **事件与指标互证**：K8s 事件 `fact-e9927254bfca` 明确报告 Secret 缺失，Metric `fact-09a4aed4d92e` 证实容器处于 `ContainerCreating` 等待态，两者一致指向挂载阶段阻塞。
*   **配置与现象关联**：K8s 配置 `fact-f991793e01cd` 显示重启数为 0，说明问题发生在容器启动前的初始化阶段（挂载卷），与 `FailedMount` 事件逻辑一致。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间缺失 Secret 'unavailable-input' → kubelet 挂载卷 'input' 失败 → Pod 阻塞于 ContainerCreating/Pending → 容器无法启动，无流量
```

### 根因结论

已确认根因：**Pod Spec 引用的 Secret `unavailable-input` 在命名空间 `aiops-case-v04` 中不存在**。

这一事实被以下证据充分支持：
1.  **K8s 事件** (证据 #2 `fact-e9927254bfca`) 直接报出 `secret "unavailable-input" not found`。
2.  **Pod 状态** (证据 #1 `fact-c7725cb43807`) 处于 `Pending`，且 **指标** (证据 #4 `fact-09a4aed4d92e`) 显示 `ContainerCreating` 原因。
3.  **配置** (证据 #3) 确认了该 Secret 是 Pod 卷挂载的必要依赖。

缺失决定性事实以解释 Secret 消失的原因（如是否被意外删除或应部署在其他命名空间），但这不影响当前故障的直接根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 32.5s
├─ 并发证据采集: 127.7s
│  └─ g1 aiops-case-v04/workload: 127.7s (Evidence 119.5s, RCA 8.1s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
