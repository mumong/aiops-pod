## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 卡在 ContainerCreating 阶段，状态为 Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态：`Pending`，Phase：`Pending`，`ContainersReady`：`False` | 确认 Pod 处于异常阻塞阶段 |
| 2 | K8s Event | kubernetes | `FailedMount`：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (最近 75s 内出现 8 次) | 直接揭示容器启动受阻的具体失败原因 |
| 3 | K8s Config | kubernetes | Volume `input` 引用 ConfigMap；但实际获取时返回 `NotFound` | 确认证卷依赖配置与实际存储资源不匹配 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}`：`1` (当前值 1) | 从监控维度独立印证容器正处于等待启动状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`：`0` (当前值 0) | 确认容器尚未启动过，排除了因 CrashLoopBackOff 或重启导致的阻塞可能 |

证据 2 中的 `FailedMount` 事件与证据 3 中获取 ConfigMap 失败的真实结果高度一致，共同证实了卷挂载失败的事实。证据 1、4、5 从 Pod 状态、容器等待原因和重启次数三个维度提供了独立的正交观测，一致指向“因外部依赖缺失导致容器无法启动”的结论。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Kubelet 挂载卷失败(FailedMount) → Pod 卡在 ContainerCreating → 业务容器无法启动
```

### 根因结论

**已确认的根因**：Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` 无法启动的直接原因是其定义的 Volume `input` 引用了一个不存在的 ConfigMap `unavailable-config`（证据 #2、#3）。Kubelet 在尝试挂载该卷时因找不到资源而持续报错 `FailedMount`，导致容器永远无法跨过 `ContainerCreating` 状态（证据 #1、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.3s
├─ 并发证据采集: 63.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 63.0s (Evidence 54.8s, RCA 8.1s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-config-error
