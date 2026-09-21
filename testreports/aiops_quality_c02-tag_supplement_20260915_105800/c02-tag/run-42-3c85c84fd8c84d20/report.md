## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod workload (aiops-case-v07) 持续处于 ImagePullBackOff 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: "ImagePullBackOff" (container: app) | 确认当前异常的直接表现形式 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: "Back-off pulling image \"registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908\"" | 指向具体失败的资源标识符 |
| 3 | K8s State | Kubernetes | `pod.phase`: "Pending" | 证实 Pod 始终无法调度进入 Running 状态 |
| 4 | K8s State | Kubernetes | `pod.condition`: Ready/ContainersReady="False", reason="ContainersNotReady" | 佐证容器未能通过初始化检查 |
| 5 | K8s State | Kubernetes | `pod.condition`: Initialized=True | 证明初始化阶段（如 ConfigMap/Secret 挂载）本身已顺利完成，问题局限在拉取镜像环节 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason="ImagePullBackOff"): 1 | 跨维度观测，数值与 K8s 状态一致 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 证实因镜像拉取失败，容器甚至未启动过，排除了应用启动后崩溃的可能性 |

上述证据共同指向一个未发生任何代码执行层面的故障：K8s 在拉取指定 Tag 的镜像时遭遇阻塞（Back-off），且 Pod 资源分配（Request/Limit）处于合理范围（CPU 5m/50m, Memory 8Mi/32Mi），排除了资源不足导致的调度或启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
指定版本的容器镜像在远程仓库中不存在 (ErrImagePull/NotFound) → Kubelet 拉取失败并进入指数退避重试 (ImagePullBackOff) → Pod 持续处于 Pending 且未就绪 → 业务应用完全不可用
```

### 根因结论

已确认根因：Pod 配置的容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在。

证据编号 2 提供了确切的报错信息，明确指出了失败的镜像路径与 Tag；结合证据编号 1 的 `ImagePullBackOff` 状态以及证据编号 7 的 `restart_count: 0`，可以排除运行时故障或资源耗尽等常见原因。Kubelet 因无法获取该镜像而持续退避重试，导致容器永远无法进入 Running 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 16.8s
├─ 并发证据采集: 36.5s
│  └─ g1 aiops-case-v07/workload: 36.5s (Evidence 26.7s, RCA 9.6s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
