## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (container: app) | 确认容器处于配置错误导致的等待状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供导致配置失败的精确缺失 Key 及 Secret 名称 |
| 3 | K8s Event | Kubernetes | `Normal Pulled`: Container image `xnet.registry.io:8443/observability/python:3-alpine` already present (x418 over 90m) | 排除镜像拉取失败，确认为本地镜像拉取成功 |
| 4 | K8s State | Kubernetes | `pod.phase`: `Pending`, `ContainersReady`: `False`, `Ready`: `False` | 验证 Pod 整体处于 Pending 且不可用状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}`: `1` | 独立指标确认 Pod 等待原因为 CreateContainerConfigError |

当前 Kubernetes 事件与状态已明确指示配置引用失败，且镜像拉取正常。Metric 独立确认了该等待原因。Logging 和 Tracing 工具调用因权限或执行失败（Forbidden），但鉴于容器未启动，缺乏业务日志符合预期，不作为关键缺失项。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key` → 
Kubernetes 校验并报错 → 
kubelet 抛出 CreateContainerConfigError 阻止容器启动 → 
Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置请求了一个在 Secret `aiops-case-04/workload-input` 中实际不存在的 Key（`unavailable-key`）。

这直接导致了 `CreateContainerConfigError`，使得容器无法启动且 Pod 始终处于 Pending 状态（证据 1、2、4、5）。Kubernetes 事件明确指出无法找到该 Key（证据 2），排除了镜像拉取问题（证据 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 15.8s
├─ 并发证据采集: 66.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 66.7s (Evidence 58.3s, RCA 8.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
