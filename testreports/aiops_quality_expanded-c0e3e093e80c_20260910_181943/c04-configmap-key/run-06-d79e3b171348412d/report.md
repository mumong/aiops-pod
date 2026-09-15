## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 阶段，容器 app 等待状态且 Reason 为 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_message: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 根因证据：明确指出了配置缺失的具体键名和 ConfigMap 名称 |
| 2 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 根因证据：确认该错误由 kubelet 触发，且重复发生 12 次 (21m) |
| 3 | K8s State | Kubernetes | container.waiting_reason: `CreateContainerConfigError` | 根因证据：容器因配置拉取失败处于等待状态 |
| 4 | K8s State | Kubernetes | pod.phase: `Pending`, pod.status: `Pending` | 现象证据：Pod 停留在调度与启动阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 | 现象佐证：指标数据确认当前存在一个容器处于该等待状态 |

上述证据均指向同一配置项缺失事实。Kubernetes 的状态和事件明确指出了因 ConfigMap 缺少特定 key (`unavailable-key`) 导致 `CreateContainerConfigError`，指标进一步量化了该异常状态的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 ConfigMap Key → Kubelet 配置拉取失败 → CreateContainerConfigError → Pod 持续 Pending
```

### 根因结论

已确认的根因为：Pod 的容器环境变量配置引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`。

这一配置错误导致 kubelet 在创建容器阶段无法获取必要的配置信息，从而直接引发 `CreateContainerConfigError` 异常（见证据 #1, #2, #3），使得 Pod 无法启动并维持 Pending 状态（见证据 #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 16.1s
├─ 并发证据采集: 564.2s
│  └─ g1 aiops-case-v11/workload: 564.2s (Evidence 555.4s, RCA 8.7s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
