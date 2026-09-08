## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 进入 CreateContainerConfigError 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod phase: Pending | 描述 Pod 整体处于挂起状态 |
| 2 | K8s State | Kubernetes | Container `app` waiting reason: CreateContainerConfigError | 指明容器创建失败的具体错误类型 |
| 3 | K8s Event | Kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接证据，指向 Secret 挂载时键值缺失 |
| 4 | K8s State | Kubernetes | Container `app` waiting message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 状态层面的错误描述，与 Event 信息一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 在 reason=`CreateContainerConfigError` 时值为 1 | 佐证容器处于创建配置错误状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 0 | 证实容器未能成功启动，无重启记录 |

**证据分析说明：**
Kubernetes 事件 (fact-aa8dc1b1be67) 提供了最核心的失败原因，直接指出 `unavailable-key` 在 Secret `aiops-case-04/workload-input` 中不存在。该事件与 K8s State 中的等待原因 (fact-1e8d087a57d8) 和等待消息 (fact-f276dd116287) 形成了完整的证据链。Metrics (fact-87e12aef62f7) 作为辅助观测，确认了该状态在 Prometheus 侧的一致性；重启数为 0 (fact-32bec44d91de) 佐证了 Pod 从未成功进入运行阶段。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 错误引用 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key` → Kubelet 无法从 Secret 获取数据导致 volume 挂载失败 → 容器启动流程被阻断 (CreateContainerConfigError) → Pod 状态停留在 Pending，app 容器无法启动
```

### 根因结论
已确认根因为 **Pod 配置错误引用了不存在的 Secret Key**。

Pod `workload-6584f97c76-7ds5p` 的 `app` 容器在启动阶段，其 Volume 或 Environment 变量配置中引用了 Secret `aiops-case-04/workload-input` 中的键 `unavailable-key`。由于该键在目标 Secret 中不存在，Kubelet 在拉取容器镜像后、启动容器进程前，无法完成该配置项的注入，从而触发 `CreateContainerConfigError` 导致 Pod 处于 Pending 状态 (fact-1e8d087a57d8, fact-f276dd116287)。

未确认：
- Secret `aiops-case-04/workload-input` 中实际存在的键列表，需人工核对以确认正确的键名。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 28.0s
├─ 并发证据采集: 31.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 31.4s (Evidence 22.9s, RCA 8.4s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
