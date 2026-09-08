## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器等待原因为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Type: Normal, Reason: Pulled, Message: Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine` | 证实镜像已成功拉取，排除网络或镜像仓库问题。 |
| 2 | K8s State | Kubernetes | `container: app, waiting_reason: CreateContainerConfigError` | 明确容器卡在配置阶段，无法进入 Running 状态。 |
| 3 | K8s State | Kubernetes | `container: app, waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接定位失败原因：Secret 中缺省关键配置项。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 确认该 Pod 处于异常等待状态的当前指标值。 |

**证据印证说明：**
Kubernetes 指标（#4）与 K8s 状态（#2）共同确认了 `CreateContainerConfigError` 现象，而事件（#1）排除了镜像拉取故障，最终由 K8s 状态中的详细消息（#3）锁定了具体的 Secret 键值缺失问题。由于容器未启动，Log 和 Tracing 数据不适用。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺少 key 'unavailable-key' → Pod Spec 引用了不存在的 Secret key 且校验失败 → kubelet 拒绝创建容器 → Pod 持续处于 CreateContainerConfigError 状态
```

### 根因结论

已确认的根因为 **Pod 配置中引用的 Secret key 不存在**。具体而言，Pod `aiops-case-04/workload-6584f97c76-7ds5p` 在配置中指定了使用 Secret `aiops-case-04/workload-input` 中的 `unavailable-key`，但该 Secret 对象中并未定义此 key（证据 #3），导致 Kubelet 校验失败并拒绝启动容器（证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 58.1s
├─ 问题定位: 19.3s
├─ 并发证据采集: 31.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 31.2s (Evidence 24.7s, RCA 6.4s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
