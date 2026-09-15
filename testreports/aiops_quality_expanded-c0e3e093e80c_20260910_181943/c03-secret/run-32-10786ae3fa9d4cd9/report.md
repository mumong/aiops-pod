## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 ContainerCreating (Pending) 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v04/workload` 状态 `Pending`，Pod Phase `Pending` (fact-6160a62eba00, fact-f3e4ffcd965b) | 确认 Pod 尚未进入运行阶段，阻塞在启动前 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount`: `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` (fact-76c0d921af38) | **直接证据**：指出因 Secret 缺失导致 Volume 挂载失败 |
| 3 | K8s Event | Kubernetes | `Warning FailedMount`: `timed out waiting for the condition` (多次重试，fact-56009950aa33) | 佐证挂载动作持续失败并超时 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` (fact-77c8e9d752a7) | 确认容器等待原因确认为 ContainerCreating |
| 5 | K8s Config | Kubernetes | 资源配置限制 `Memory: 32Mi`, `CPU: 50m` (fact-0c7df41b9426, fact-133f3b45aefa) | 排除资源超限导致的 OOMKilled 或限制类等待 |
| 6 | K8s State | Kubernetes | 容器重启计数 `0` (fact-3222a1d2be18) | 确认容器从未成功启动，排除运行中崩溃 |

**证据说明**：
1. Kubernetes 状态（fact-6160a62eba00, fact-f3e4ffcd965b）与 Prometheus 指标（fact-77c8e9d752a7）一致确认 Pod 处于 `Pending` 且容器处于 `ContainerCreating` 等待状态。
2. 关键证据为 `FailedMount` 事件（fact-76c0d921af38），明确指向引用不存在的 Secret `unavailable-input`。
3. 持续超时的挂载事件（fact-56009950aa33）与重启计数为 0（fact-3222a1d2be18）共同表明，Pod 在挂载阶段即被阻塞，未能进入应用容器启动逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 Secret 'unavailable-input' → Secret 对象缺失导致 Volume 挂载失败 → Kubelet 阻塞在 VolumeMount 阶段 → Pod 状态卡在 Pending/ContainerCreating
```

### 根因结论

已确认的根因为：**Pod `aiops-case-v04/workload` 定义的 Volume `input` 引用了不存在的 Secret `unavailable-input`，导致挂载操作持续失败。**

依据：
- Kubernetes 事件 `FailedMount` (fact-76c0d921af38) 明确指出 `secret "unavailable-input" not found`。
- 状态机显示 Pod 处于 `Pending` (fact-6160a62eba00)，容器等待原因为 `ContainerCreating` (fact-77c8e9d752a7)，且重启次数为 0 (fact-3222a1d2be18)，符合启动前依赖缺失的特征。

未确认问题：Secret `unavailable-input` 为何未被创建或意外删除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.4s
├─ 并发证据采集: 34.0s
│  └─ g1 aiops-case-v04/workload: 33.9s (Evidence 23.6s, RCA 10.2s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
