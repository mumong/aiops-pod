## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 Pending 状态，容器 app 报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: `CreateContainerConfigError`, container.waiting_message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指向容器启动配置引用失败的具体缺失对象 |
| 2 | K8s State | Kubernetes | pod.status: `Pending`, pod.phase: `Pending` | 确认 Pod 未进入运行状态 |
| 3 | K8s Event | Kubernetes | `Normal Pulled ... Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine` (x280) | 证实镜像拉取成功且环境正常，排除了镜像拉取失败的可能 |
| 4 | K8s Event | Kubernetes | `ContainersReady: False`, `Ready: False`, containers with unready status: [app] | 佐证容器未启动状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError", container="app"} = 1` | 独立维度确认容器处于创建配置错误的等待原因 |
| 6 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 独立维度确认 Pod 处于 Pending 阶段 |
| 7 | K8s Config | Kubernetes | container.resource_request.memory: `8Mi`, container.resource_limit.memory: `32Mi` | 确认资源限制存在，非资源不足导致的调度或启动失败 |

上述证据中，K8s 原始状态（#1）精确指出了 `Secret aiops-case-04/workload-input` 中缺少 `unavailable-key` 导致 `CreateContainerConfigError`；同时镜像拉取事件（#3）和 Metric 指标（#5, #6）从独立维度排除了网络、镜像、调度等上游问题，强有力地证实了该配置错误是导致 Pod 停留在 Pending 状态的唯一原因。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 缺失 key 'unavailable-key' → 容器启动时无法获取配置导致 kubelet 返回 CreateContainerConfigError → Pod 处于 Pending 状态，容器不启动
```

### 根因结论

已确认的根因是 Pod 的容器定义中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 实际上并不包含此 key。这直接导致 kubelet 在启动容器时无法获取必要的配置信息，从而抛出 `CreateContainerConfigError`（证据 #1, #5），并导致 Pod 一直卡在 `Pending` 状态（证据 #2, #6）。

**待确认问题：**
输入中未提供 Secret `aiops-case-04/workload-input` 的实际内容事实，因此无法进一步确认该 Secret 中实际包含了哪些 key（仅根据报错逻辑推测可能存在 `available-key`），也无法解释为何 Secret 创建时未包含预期的 `unavailable-key`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 22.3s
├─ 并发证据采集: 59.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 59.2s (Evidence 48.8s, RCA 10.2s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
