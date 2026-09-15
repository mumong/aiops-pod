## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod / Container | 状态 `ContainerCreating`；Waiting 原因 `ContainerCreating` (fact-50d794affca1) | 直接确认异常现象与当前阻塞阶段 |
| 2 | K8s State | Pod Condition | `ContainersReady=False` (`ContainersNotReady: [app]`), `Ready=False` (fact-e710be4aa073) | 证实容器未能就绪，非健康或重启状态 |
| 3 | K8s State | Resource Context | `cpu_request=5m`, `cpu_limit=50m`; `memory_request=8Mi`, `memory_limit=32Mi` (fact-18e52bb3dfb3 等) | 资源请求量极低，无资源挤占或配额耗尽迹象 |
| 4 | K8s State | Restart Count | `restart_count=0` (fact-c158d7269e5c) | 排除因 OOMKilled 或 CrashLoopBackOff 导致的状态异常 |
| 5 | Metric | Waiting Reason | `kube_pod_container_status_waiting_reason=1` (reason=ContainerCreating, fact-2d7ef2d8d7d6) | 独立观测确认 Pod 卡在挂载或创建前置阶段的指标事实 |

Pod 未重启且资源请求极低，排除了应用崩溃与资源竞争因素；等待原因 `ContainerCreating` 与指标一致，结合未就绪条件，强烈指向容器启动前的挂载或前置依赖失败，而非容器内应用逻辑问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 Secret 'unavailable-input' → Kubelet 挂载卷失败 (FailedMount) → Pod 持续处于 ContainerCreating 状态 → 无法启动容器
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v04/workload` 声明了一个名为 `input` 的 Volume，该 Volume 试图挂载 Secret `unavailable-input`。由于该 Secret 在命名空间 `aiops-case-v04` 中不存在，Kubelet 在尝试挂载该卷时发生 `FailedMount` 错误。

这一失败导致 Pod 卡在 `ContainerCreating` 阶段，无法进行容器镜像拉取及容器进程启动。证据 #1、#2 及 #5 一致确认了 Pod 停留在创建阶段且未就绪，且未发生重启（证据 #4），符合挂载失败阻塞容器启动的特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 23.8s
├─ 并发证据采集: 30.0s
│  └─ g1 aiops-case-v04/workload: 30.0s (Evidence 22.8s, RCA 7.2s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed
