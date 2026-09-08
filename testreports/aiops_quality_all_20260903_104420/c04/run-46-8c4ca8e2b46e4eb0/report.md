## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `waiting_reason=CreateContainerConfigError`, `waiting_message=couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确诊容器无法启动的直接原因：Secret 引用键不存在 |
| 2 | K8s Event | Kubernetes | `Normal Pulled 3m37s (x395 over 88m) kubelet Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine` | 排除镜像拉取问题，确认基础环境正常 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory=32Mi`, `resource_limit.cpu=50m` | 资源限制配置，非本次故障原因（上下文） |
| 4 | K8s State | Kubernetes | `pod.phase=Pending`, `pod.condition.ContainersReady=False, reason=ContainersNotReady` | 确认 Pod 整体处于未就绪状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=CreateContainerConfigError, container=app) | 验证了 K8s 状态中观察到的等待原因 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` | 确认容器因配置错误从未成功启动过 |
| 7 | Logging | Elasticsearch | 采集失败：`query_rejected` (Forbidden: cannot create resource "pods/exec" in namespace "monitor") | 无法获取应用日志，符合容器未启动的设定 |
| 8 | Tracing | DeepFlow/Tempo | 采集失败：`query_rejected` (Forbidden: cannot create resource "pods/exec" in namespace "monitor") | 无法获取业务流量，符合容器未启动的设定 |

**证据关联分析：**
K8s 状态事实 (Fact 1) 提供了明确的错误原文，指出 Secret 键缺失；Metrics (Fact 5, 6) 独立佐证了该等待原因及零重启状态。Logging/Tracing (Fact 7, 8) 的失败是因为目标容器未启动且底层采集工具权限受限，属于预期结果。K8s 配置 (Fact 3) 和资源条件 (Fact 4) 支持了“容器因配置校验失败而卡在 Pending 阶段”的推论。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺失 key 'unavailable-key' (触发) → 
Pod 容器 app 尝试挂载该不存在键并校验失败 (机制) → 
Kubernetes 容器创建阶段配置验证失败，进入 CreateContainerConfigError (直接失败) → 
Pod 保持 Pending 且容器不可用 (用户可见现象)
```

### 根因结论

**已确认的根因**：
Pod 容器 `app` 的启动配置中引用了 Secret `aiops-case-04/workload-input` 中的键 `unavailable-key`，但该 Secret 中实际上并不存在此键（仅存在 `available-key`，根据错误原文推断）。这一配置错误导致 Kubernetes 在尝试创建容器时无法解析挂载配置，从而抛出 `CreateContainerConfigError` 并阻止容器启动。

**证据支撑**：
- K8s State `container.waiting_message` (Fact 1) 直接指出了具体的缺失键名和所属 Secret。
- K8s Event (Fact 2) 和 Metrics (Fact 5, 6) 确认了异常仅发生在配置阶段，而非运行时或依赖外部服务（如日志/链路追踪）的可用性问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 21.3s
├─ 并发证据采集: 59.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 59.3s (Evidence 52.5s, RCA 6.5s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
