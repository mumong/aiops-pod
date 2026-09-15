## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload stuck in ContainerCreating/Pending phase |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | fact-3beb05b81f61: `FailedMount` `timed out waiting for the condition` (x10 over 23m) | 确认挂载动作已发生超时阻塞 |
| 2 | K8s Event | kubernetes | fact-bd835ccdb61f: `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 明确根因为 Secret 缺失导致挂载失败 |
| 3 | K8s State | kubernetes | fact-0962ce8e6303: `ContainerCreating` (app) | 容器持续卡在创建阶段，未进入运行状态 |
| 4 | K8s State | kubernetes | fact-3739a7a8be6d: `Pending` (Pod Status) | Pod 处于调度后、调度失败阻塞状态 |
| 5 | Metric | prometheus | fact-896bc7265293: `kube_pod_container_status_waiting_reason` `ContainerCreating` (app) | 指标数值为 1，客观印证容器处于等待挂载或拉取状态 |

**证据分析说明：**
1. K8s 事件 (fact-2, fact-1) 直接指出了故障的具体物理原因：`secret "unavailable-input"` 不存在，导致 `FailedMount`。
2. K8s 状态 (fact-3, fact-4) 与 指标 (fact-5) 均一致显示容器因挂载阻塞而处于 `Pending` 和 `Waiting(ContainerCreating)` 状态，未发生重启。
3. 资源配置 (CPU 50m / Mem 32Mi) 无极端异常，且资源请求与挂载失败无直接因果，故作为上下文略去详细展示。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 Secret 'unavailable-input' (fact-2) 
→ kubelet 尝试挂载 volume 'input' 失败 
→ 直接触发 FailedMount 事件 (fact-1) 
→ 容器 'app' 无法启动，Pod 卡在 ContainerCreating/Pending 状态 (fact-3, fact-4, fact-5)
```

### 根因结论

已确认的根因为：**Pod 的 Volume 定义引用了名为 `unavailable-input` 的 Secret，但该 Secret 在 `aiops-case-v04` 命名空间中不存在。**

证据表明，kubelet 在启动容器前必须挂载此 volume，因 Secret 缺失导致挂载持续失败（超时 x10），进而使得容器进入 `Waiting` 状态。此结论由 `FailedMount` 事件原文 (fact-2) 直接支撑，且与 Pod 状态 (fact-4) 及 Metric 指标 (fact-5) 完全一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 31.2s
├─ 并发证据采集: 44.0s
│  └─ g1 aiops-case-v04/workload: 44.0s (Evidence 35.9s, RCA 8.0s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
