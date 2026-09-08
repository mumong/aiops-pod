## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` | 确认 Pod 处于配置注入失败状态，无法启动应用容器 |
| 2 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出失败原因为 Secret 中缺失特定的 Key |
| 3 | K8s Event | kubernetes | `Normal Pulled`: 容器镜像 `xnet.registry.io:8443/observability/python:3-alpine` 已存在于机器上 | 排除镜像拉取失败的可能性，证明网络与镜像仓库正常 |
| 4 | K8s State | kubernetes | `pod.condition`: `ContainersReady=False`, `Ready=False`, `PodScheduled=True`, `Initialized=True` | 证实 Pod 生命周期卡在初始化阶段，且未被调度失败或资源不足阻断 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory`: `8Mi`, `container.resource_limit.memory`: `32Mi` | 确认资源请求量极小，排除因资源不足导致创建失败的可能 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 值为 `1` (标签 `reason=CreateContainerConfigError`, `container=app`) | 从指标层面交叉验证容器正处于配置错误等待状态 |

证据之间高度一致：Kubernetes 状态机直接报出 `CreateContainerConfigError`，且消息明确指向 `Secret` 中缺失 `unavailable-key`；同时 `kubelet` 已成功拉取镜像并尝试启动容器，说明底层基础设施（如 CNI、镜像仓库）无异常。Metric 数据在时间窗口内一致反映了该等待状态，排除了瞬时抖动。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 中缺少 key 'unavailable-key' → kubelet 注入 Secret 数据失败 → 容器处于 CreateContainerConfigError 状态 → Pod 持续 Pending，应用不可用
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 Spec 中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中实际不存在此 key。

这一不匹配直接导致 kubelet 在尝试注入配置时失败，容器引擎拒绝启动该容器，从而产生 `CreateContainerConfigError` 状态（见证据 1, 2, 6）。由于容器始终无法进入运行状态，Pod 保持 `Pending`，应用完全不可用。证据链完整，无需补充额外日志或追踪数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.7s
├─ 并发证据采集: 74.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 74.8s (Evidence 65.8s, RCA 8.8s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
