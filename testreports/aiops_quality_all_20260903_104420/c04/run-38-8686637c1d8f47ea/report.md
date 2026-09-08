## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 状态为 Pending，容器 app 处于 Waiting (CreateContainerConfigError)，0 次重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.app.waiting_reason=CreateContainerConfigError`; `pod.phase=Pending` | 核心异常状态，明确容器处于配置注入失败导致的等待状态 |
| 2 | K8s Event | Kubernetes | `message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接归因事实，指出 Secret 中缺少 Key 导致配置注入失败 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=`CreateContainerConfigError`) | 监控数据印证 Kubernetes 中的异常状态，排除了其他 Waiting 原因 |
| 4 | K8s State | Kubernetes | `pod.condition.ContainersReady=False`; `pod.condition.Ready=False` | 状态同步确认，Pod 因容器未就绪而无法提供服务 |
| 5 | Metric | Prometheus | `kube_pod_status_phase=1` (phase=`Pending`) | 监控确认 Pod 整体停留在 Pending 阶段 |

**证据说明：**
- 事实 #1 和 #3 互相印证了 Pod 处于 `CreateContainerConfigError` 状态，且排除了资源不足等其他 Waiting 原因。
- 事实 #2 提供了具体的失败机制，证实了 K8s 事件日志直接指向 Secret 配置引用错误，是决定性的根因证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 错误引用 Secret key 'unavailable-key' → Secret 'aiops-case-04/workload-input' 实际不包含该 key → Kubelet 注入配置失败，报错 CreateContainerConfigError → 容器 app 处于 Waiting 状态，Pod 无法进入 Running
```

### 根因结论

已确认的根因为 **Pod spec 配置错误**：容器 `app` 引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。

**证据支撑：**
- 事实 #2 明确指出 Kubelet 无法找到该 Key，这是导致 `CreateContainerConfigError` 的唯一原因。
- 事实 #1、#3、#4 全面验证了该配置错误导致的最终状态（容器 Waiting、Pod Pending、未就绪）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 24.2s
├─ 并发证据采集: 53.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 53.5s (Evidence 43.6s, RCA 9.8s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
