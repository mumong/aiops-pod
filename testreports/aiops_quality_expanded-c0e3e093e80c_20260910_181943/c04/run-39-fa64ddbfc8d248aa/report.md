## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 持续处于 Pending 状态，状态码为 CreateContainerConfigError，容器未能启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `event.message`: "Normal Pulled 3m28s (x282 over 63m) kubelet Container image already present on machine" (fact-ff6809436544) | 确认镜像拉取阶段无网络或鉴权异常，排除网络类故障 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (fact-831d8544d5fb) | 直接证据，指明 Secret 资源访问的具体失败点与错误键 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: "CreateContainerConfigError" (fact-66a6e5d09d5c) | 确立异常类型，表明问题发生在环境变量注入阶段，早于容器启动 |
| 4 | K8s State | Kubernetes | `pod.status`: "Pending" (fact-47df23639e98) | 确认 Pod 处于未就绪状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, labels: {reason: "CreateContainerConfigError"} (fact-b732d2d0b6b9) | 跨维度观测验证 K8s 侧记录的 CreateContainerConfigError 状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-c859475fccf9) | 确认容器从未成功启动过，无启动后异常重启现象 |

**证据关联说明：**
Kubernetes `WaitingMessage` 明确指出因找不到 Secret 键导致 `CreateContainerConfigError`；Metric 数据同步反映了该等待状态的持续存在及零重启；日志与追踪数据因容器未启动而未产生有效记录，排除运行时异常。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 配置错误 (引用了不存在的 Key) → Kubelet 注入环境变量失败 → 容器创建被拦截 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod Spec 配置错误**。Pod `workload-6584f97c76-h4lt9` 尝试从 Secret `aiops-case-04/workload-input` 中读取 Key `unavailable-key` 作为环境变量，但该 Key 在 Secret 中不存在且未配置为 `optional` 模式。这导致 Kubelet 在创建容器前无法完成配置注入，从而直接报 `CreateContainerConfigError` 错误并终止容器启动（证据编号 2, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.9s
├─ 并发证据采集: 54.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 54.2s (Evidence 46.1s, RCA 8.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
