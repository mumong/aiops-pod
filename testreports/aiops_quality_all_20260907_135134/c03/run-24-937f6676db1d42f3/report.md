## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 持续处于 ContainerCreating/Pending 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-70967851aec9) | `FailedMount` 11m (x23 over 42m) : configmap "unavailable-config" not found | 直接指出 Pod 因找不到 ConfigMap 'unavailable-config' 导致挂载卷失败 |
| 2 | K8s State | kubernetes (fact-a538b1b81171) | status: Pending | 证实 Pod 处于未就绪状态 |
| 3 | K8s Config | kubernetes (fact-619edc5e4fc2) | container.resource_limit.memory: 32Mi | 资源上下文：容器内存限制极低，非本次启动失败主因 |
| 4 | Metric | prometheus (fact-988f6b884c68) | kube_pod_container_status_waiting_reason: 1 (reason: ContainerCreating) | 从 Prometheus 侧证实容器处于等待启动阶段 |

**证据印证说明：**
K8s Event 记录了具体的挂载失败原因（ConfigMap 缺失）及高频重试次数（x23 over 42m），与 Pod 状态（Pending）和 Metric 状态（Waiting for ContainerCreating）形成闭环，确认为启动阻塞类故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义引用不存在的 ConfigMap 'unavailable-config' (非 Optional) → 挂载卷失败 (FailedMount) → Pod 持续 Pending / ContainerCreating → 容器无法启动
```

### 根因结论

**已确认根因：** 容器 `workload-5b5fc86c8c-2xgjz` 卡在 `ContainerCreating/Pending` 状态的根本原因是 **挂载卷失败**。
证据显示 Kubelet 持续报出 `FailedMount` 错误，明确指出 `configmap "unavailable-config" not found`。由于该 ConfigMap 在命名空间 `aiops-case-03` 中不存在且配置为强制依赖，导致挂载卷初始化超时，容器无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 57.4s
├─ 问题定位: 22.3s
├─ 并发证据采集: 27.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 27.7s (Evidence 20.5s, RCA 7.1s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed, pod-config-error, pod-imagepull-failed
