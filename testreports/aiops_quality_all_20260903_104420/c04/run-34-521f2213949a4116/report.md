## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 Pending 状态，持续报 CreateContainerConfigError 异常。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-00666f2454c4` | `container.resource_limit.cpu`: `50m` | 确认容器运行资源限制配置正常，非资源超限。 |
| 2 | K8s State | `fact-0806cd43934c` | `container.waiting_reason`: `CreateContainerConfigError` | 直接定位到容器配置层面的失败原因。 |
| 3 | K8s State | `fact-04c9a85f7d7f` | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确凿的失败机制：Secret 挂载时 key 不存在。 |
| 4 | K8s State | `fact-61403f05d926` | `pod.status`: `Pending` | 确认 Pod 因配置校验失败始终处于 Pending 状态。 |
| 5 | K8s State | `fact-8b5d927f605a` | `container.restart_count`: `0` | 确认未发生重启，进一步佐证为初始化配置校验未通过而非运行时问题。 |
| 6 | K8s Event | `fact-12dc731544ff` | `event.message`: `Normal Pulled 4m1s ... Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine` | 确认容器镜像拉取成功，排除镜像源问题。 |
| 7 | Metric | `fact-d6f288d050aa` | `kube_pod_container_status_waiting_reason`: 值为 `1` (Labels: `container="app", reason="CreateContainerConfigError"`) | 时序数据与 K8s 事件状态高度一致。 |

**证据关联说明：**
证据 2、3、5、6 在 Kubernetes 层面形成闭环，确凿证明镜像拉取成功但挂载 Secret 因 key 缺失导致初始化失败；证据 1 排除资源限制干扰；证据 7 的 Metric 数据与 K8s 状态（证据 2）相互印证。Logging 与 Tracing 因容器未启动不可用（`not_applicable`）。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用 Secret 中不存在的 key 'unavailable-key' → kubelet 校验 Secret 挂载依赖失败 → 容器无法创建，状态变为 CreateContainerConfigError → Pod 持续处于 Pending 状态
```

### 根因结论
已确认根因为 **配置错误**。Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 Spec 配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，导致 kubelet 在初始化阶段校验 Secret 挂载依赖失败，进而引发 `CreateContainerConfigError`，使容器无法创建，Pod 持续处于 Pending 状态（见证据 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.9s
├─ 并发证据采集: 44.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 44.7s (Evidence 36.9s, RCA 7.6s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
