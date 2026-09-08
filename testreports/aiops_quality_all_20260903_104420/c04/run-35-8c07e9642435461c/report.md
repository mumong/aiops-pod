## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 Pending 状态，容器 app 处于 Waiting 状态，Reason 为 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Pending (fact-6fa7ff42bf4d) | 确认 Pod 处于未就绪状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CreateContainerConfigError (fact-5c7eceabc77b) | 标识容器创建阶段的具体失败类型 |
| 3 | K8s State | kubernetes | `container.waiting_message`: couldn't find key unavailable-key in Secret aiops-case-04/workload-input (fact-abeafac4a33a) | 直接指出配置加载失败的根本原因：密钥缺失 |
| 4 | K8s Event | kubernetes | Normal Pulled (x326 over 70m) (fact-48d9045a8d74, fact-5e04655af39b) | 排除镜像拉取失败，确认网络及镜像仓库正常 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=CreateContainerConfigError) 值为 1 (fact-6277ff5f6e3c) | 指标层面确认当前等待状态，支持 K8s 状态观测 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 (fact-8d99798f5ae0) | 确认无重启行为，符合创建配置失败的预期 |

**证据说明：**
Kubernetes 的 `Waiting Reason` 与 `Waiting Message`（证据 2、3）直接锁定了配置加载失败的根因为 Secret 中缺少指定 Key。Metric 数据（证据 5、6）在数值上复现了该状态且无重启，排除了容器因 OOM 或健康检查失败而 CrashLoopBackOff 的可能。K8s Event（证据 4）证明镜像拉取成功，排除了运行时网络或镜像问题。

## 🎯 根因分析 · g1

### 因果链
```text
Secret aiops-case-04/workload-input 中不存在 'unavailable-key' → 容器启动时 Kubelet 解析配置失败 → 拒绝创建容器 (CreateContainerConfigError) → Pod 保持 Pending 状态
```

### 根因结论
已确认根因为 Pod 定义中引用的 Secret `aiops-case-04/workload-input` 中缺失了所需的 `unavailable-key`（见证据 #3）。Kubelet 在尝试注入配置时因找不到该键而报错，导致容器无法启动。证据 #4 证明镜像拉取正常，证据 #5 和 #6 确认了该配置错误持续存在且未引发后续重启。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.1s
├─ 并发证据采集: 50.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 50.7s (Evidence 41.9s, RCA 8.6s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
