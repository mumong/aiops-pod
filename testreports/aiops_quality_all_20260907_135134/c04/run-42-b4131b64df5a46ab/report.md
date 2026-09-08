## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 'workload-6584f97c76-7ds5p' 处于 Pending 状态且容器等待原因为 'CreateContainerConfigError'，但当前采集的 'kubectl describe' 输出中仅存在 Normal 事件（Container image already present），缺失导致配置错误的核心 Warning 事件（如 Secret/ConfigMap 缺失或挂载无效的具体报错）。由于无法从现有日志、指标或拓扑中定位具体的配置资源引用缺陷，且未提供 Pod YAML 以检查 volume/env 引用，当前证据不足以确诊具体的根本原因。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-6584f97c76-7ds5p` 状态: `Pending` (fact_id: fact-d469a6e689fe) | 确认异常状态 |
| 2 | K8s Event | Kubernetes | Normal Pulled: Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine (fact_id: fact-2a4920cbd4bd) | 排除镜像拉取失败 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 1 (container=app, reason=CreateContainerConfigError) (fact_id: fact-06a75fbe58ac) | 确认容器创建配置阶段报错 |
| 4 | K8s Config | Kubernetes | Limits: memory=32Mi, cpu=50m; Requests: memory=8Mi, cpu=5m (fact_ids: fact-26228c043065, fact-3efe57e826d0, fact-4599c39da756, fact-57b3da2efef0) | 资源配置上下文 |
| 5 | K8s State | Kubernetes | `kube_pod_container_status_restarts_total` 0 (fact_id: fact-d7bb92a8b681) | 确认无重启记录，启动失败即被阻止 |
| 6 | K8s Event | Kubernetes | `kubectl describe` 仅输出 Normal 事件及网络注解，缺失导致 `CreateContainerConfigError` 的 Warning 事件 (事实描述与 fact_ids: fact-38df97810234, fact-42b48de8ca9a, fact-49fd90be3b77, fact-4e4a1f087d28, fact-8f842b6a83d5, fact-afdfdd234892, fact-c85af767f0ed) | 缺失关键故障日志 |

**证据关系说明：**
1. **确认异常但定位受阻**：Metric 和 K8s 状态明确显示容器因配置错误处于 Pending 状态（证据 1, 3），但 K8s Event 中仅存在镜像已存在的记录（证据 2），缺失直接导致配置失败的 Warning 日志（证据 6），导致无法判断具体是哪个 Secret 或 ConfigMap 引用失效。
2. **排除常见干扰项**：重启数为 0（证据 5）说明 Pod 启动过程被阻断，不存在因启动后配置错误导致的重启；资源限制极小（证据 4）是已知配置特征，但无 OOM 指标，且 `CreateContainerConfigError` 属于 Kubelet 挂载阶段的错误，非运行时资源超限。

## 🎯 根因分析 · g1

### 因果链

```text
证据不足：缺失直接导致 CreateContainerConfigError 的 Warning 事件（如 Secret/ConfigMap 缺失或无效） → 失败机制：Kubelet 挂载配置资源失败 → 直接失败：容器创建阻断 → 用户可见现象：Pod Pending, waiting reason=CreateContainerConfigError
```

### 根因结论

**证据不足，无法确诊具体根本原因。**

现有证据仅能定位故障阶段为 `CreateContainerConfigError`，并排除了镜像拉取失败。但是，关键的诊断事实（导致配置错误的 Warning Event，或 Pod YAML 中的 volume/env 定义）缺失。由于无法从当前采集的数据中识别具体的无效配置资源引用，无法确定根本原因是 Secret/ConfigMap 缺失、权限不足还是挂载路径错误。

---

## 📊 性能统计

```text
├─ 总耗时: 59.1s
├─ 问题定位: 15.7s
├─ 并发证据采集: 31.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 31.0s (Evidence 23.4s, RCA 7.5s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
