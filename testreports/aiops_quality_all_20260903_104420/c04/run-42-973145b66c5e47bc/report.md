## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 状态为 Pending，容器 app 处于 Waiting 状态，Reason 为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `status: Pending`, `container.waiting_reason: CreateContainerConfigError` | 确认 Pod 处于未就绪状态，容器启动被阻止 |
| 2 | K8s State | Kubernetes | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出失败原因为 Secret 中缺失指定 Key |
| 3 | K8s Event | Kubernetes | Normal Pulled (x372 over 82m), image `python:3-alpine` already present | 排除镜像拉取问题，佐证错误发生在配置注入阶段 |
| 4 | K8s Config | Kubernetes | `resource_request.memory: 8Mi`, `resource_limit.memory: 32Mi` | 提供资源配置上下文，排除资源配额限制导致的调度失败 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 确认异常在指标层持续存在，与 K8s 状态一致 |

**证据总结**
Kubernetes 的 Waiting 状态、错误信息及 Prometheus 指标高度一致，均指向 Secret `workload-input` 中缺失 `unavailable-key`。镜像已成功拉取且无重启记录，排除了启动后崩溃的可能。由于容器未启动，Logging 与 Tracing 数据无法采集，但不影响对该配置错误的判定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 引用了不存在的 Secret Key (`unavailable-key`) → Kubelet 解析配置失败 → 容器启动阻塞，Pod 进入 Pending 状态 → 业务应用不可用
```

### 根因结论

根因已确认。Pod `workload-6584f97c76-wvcb2` 中的容器 `app` 因配置引用了 Secret `workload-input` 中不存在的 key `unavailable-key` 而启动失败（CreateContainerConfigError）[证据 1, 2, 5]。
注：Secret 中确实缺失该 key 这一事实为配置错误或同步异常，需人工确认具体原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.5s
├─ 并发证据采集: 57.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 57.0s (Evidence 48.4s, RCA 8.4s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
