## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 的容器配置引用了 Secret 'workload-input' 中不存在的 Key 'unavailable-key'，导致 Kubelet 无法完成容器创建。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接说明 Kubelet 在挂载配置时因找不到 Secret Key 而拒绝启动容器。 |
| 2 | K8s State | Kubernetes | `container.app.waiting_reason: CreateContainerConfigError` | 标识容器未处于运行或崩溃状态，而是卡在配置验证阶段。 |
| 3 | K8s State | Kubernetes | `container.app.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 与 Event 信息一致，进一步确认等待原因为缺失的 Secret Key。 |
| 4 | K8s State | Kubernetes | `pod.phase: Pending` | 表明 Pod 尚未开始调度运行，处于待处理状态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 确认观测窗口内容器处于“等待配置错误”状态，与 K8s 状态一致。 |

**证据关联说明：**
1. K8s State (`CreateContainerConfigError`) 与 Metric (`waiting_reason`) 相互印证，确认容器未能启动并非因为 OOM 或 Crash，而是因为启动前的配置校验失败。
2. K8s Event 和 Message 提供了具体的失败细节（`unavailable-key` in `workload-input`），排除了网络或其他系统层面的问题，将根因定位在 Pod 定义对 Secret 的引用配置上。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 Secret Key 'unavailable-key' → 容器启动时配置加载失败 → Kubelet 触发 CreateContainerConfigError → Pod 保持 Pending 状态，容器不运行
```

### 根因结论

已确认的根因：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。

这一配置错误导致 Kubelet 在尝试创建容器前验证挂载配置失败，从而阻止了容器启动。该结论由 K8s Event（fact-a3d71c2492c5）和 Container Waiting Message（fact-f45939552448）直接支持，并与 Metric（fact-406f491c0dce）显示的长期等待状态一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.5s
├─ 并发证据采集: 48.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 48.3s (Evidence 43.0s, RCA 5.2s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
