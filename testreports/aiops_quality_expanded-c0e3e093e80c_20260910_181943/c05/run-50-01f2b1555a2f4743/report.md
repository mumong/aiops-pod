## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 卡在 ContainerCreating 状态 |
| g2 | `monitor/local-disk-observability-byconity-server-0` | Unknown | Pod monitor/local-disk-observability-byconity-server-0 状态为 Unknown，可观测性数据缺失 |
| g3 | `monitor/log-observability-byconity-server-0` | Unknown | monitor/log-observability-byconity-server-0 初始状态为 Unknown，无法获取日志、指标或拓扑数据。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接证实 Multus CNI 插件因找不到指定的网络定义资源而无法初始化网络 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error: ... plugin type="multus" name="multus-cni-network" failed (add): ... error in getting k8s network for pod: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) ... not found` | 证实 Pod Sandbox 创建失败的根本原因是 Multus 插件返回了上述网络缺失错误 |
| 3 | K8s State | Pod Spec (Derived) | `network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 表明 Pod 配置引用了不存在的网络附件资源 |
| 4 | K8s State | Pod Status | `reason: ContainerCreating` | 确认 Pod 当前停滞在等待阶段，与 Multus 失败导致的 Sandbox 创建阻塞现象一致 |

证据 1 和 2 明确指向 Multus 插件因依赖的 `NetworkAttachmentDefinition` 资源缺失而报错；证据 4 显示该错误直接导致 Pod 处于 `ContainerCreating` 停滞状态。

## 🎯 根因分析 · g1

### 因果链
```text
Namespace "aiops-case-05" 中缺失 Multus 网络资源 "unavailable-network" → Multus CNI 插件初始化失败 → Pod Sandbox 创建失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating
```

### 根因结论
已确认根因为 **Pod 引用的 Multus 网络附件定义资源不存在**。
证据显示 Pod 在启动时，kubelet 调用 Multus CNI 插件尝试创建网络时，因无法在 `aiops-case-05` 命名空间中找到名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，导致 Multus 报错并返回失败，从而阻断了 Pod Sandbox 的创建，使 Pod 持续处于 `ContainerCreating` 状态（参见证据 1、2、4）。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubectl_find_resource | `Command failed (exit 1): kubectl get -A --show-labels -o wide pods \| grep -i 'byconity-server'` | 排除集群中是否存在包含 byconity-server 标签的其他 Pod，证明集群中无相关实体。 |
| 2 | K8s State | kubectl_describe | `Error from server (NotFound): pods "local-disk-observability-byconity-server-0" not found` | 确认目标 Pod `monitor/local-disk-observability-byconity-server-0` 在集群中确实不存在。 |
| 3 | K8s State | execute_pod_promql | `Error from server (NotFound): pods "local-disk-observability-byconity-server-0" not found` | 说明 Prometheus 查询失败并非查询语法或指标配置问题，而是因监控对象（Pod）本身缺失导致。 |
| 4 | Logging | query_pod_logs | `Error from server (NotFound): pods "local-disk-observability-byconity-server-0" not found` | 确认 Elasticsearch 日志收集工具同样因找不到目标 Pod 而无法获取日志。 |

所有维度的工具调用（Metrics, Logging, Tracing, kubectl 查询）均返回 `NotFound` 错误或搜索无结果。不存在任何“存在但运行异常”的观测数据，所有的可观测性缺失（Metrics/Logging/Tracing）均由同一事实——Pod 实体缺失——所导致。

## 🎯 根因分析 · g2

### 因果链

```text
Pod 实体在集群中不存在（NotFound） → 可观测性查询直接拒绝 → 下游系统返回 Error → Pod 状态标记为 Unknown 及全量数据缺失
```

### 根因结论

**已确认根因：Pod `monitor/local-disk-observability-byconity-server-0` 在 Kubernetes 集群中不存在。**

当前现象（Pod 状态为 Unknown 以及 Metrics、Logs、Tracing 数据全量缺失）的根本原因是监控目标实体在集群中不存在。

- **依据**：
    - `kubectl_describe` (证据 2) 和 `kubectl_find_resource` (证据 1) 明确返回 `NotFound` 错误，证明该 Pod 未在 `monitor` 命名空间创建，或已被删除。
    - Prometheus、Elasticsearch 等可观测性后端工具的查询结果均依赖于 K8s API 获取 Pod 的当前状态或日志流。由于 Pod 不存在，这些工具无法检索到任何有效数据，因此统一报错（证据 3、4）。
    - 集群内不存在任何同名的其他 Pod 或包含 `byconity-server` 关键字的 Pod，排除了名称拼写错误或 Pod 被迁移至其他命名空间的可能性。

不存在除“实体缺失”之外的其他故障机制（如 CrashLoopBackOff、Pending 或 OOMKilled），因为没有 Pod 实例在运行。

---

## 🕵️ 证据内容 · g3

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubectl describe / kubectl get | `Error from server (NotFound): pods "log-observability-byconity-server-0" not found` (Namespace: monitor) | 确证 Pod 在当前集群中物理不存在，是所有后续查询失败的直接根源。 |
| 2 | Metric | prometheus (execute_pod_promql) | `Error from server (NotFound): pods "log-observability-byconity-server-0" not found` | 确认因实体缺失导致无法拉取 CPU/Memory 等运行时指标。 |
| 3 | Logging | elasticsearch (query_pod_logs) | `Error from server (NotFound): pods "log-observability-byconity-server-0" not found` | 确认无法检索日志数据，佐证该 Pod 已停止或被删除。 |
| 4 | Tracing | deepflow+tempo (query_pod_tracing) | `Error from server (NotFound): pods "log-observability-byconity-server-0" not found` | 确认无关联流量数据或 Span 记录，排除隐蔽的残留流量影响。 |
| 5 | Topology | kubernetes (query_pod_topology) | `Error from server (NotFound): pods "log-observability-byconity-server-0" not found` | 拓扑探测失败，进一步证实无节点分配或控制器关联。 |

所有可观测性采集工具（Metrics、Logging、Tracing、Topology）均因 Kubernetes 层面的 `NotFound` 状态而同步返回错误。这种一致性的“全量不可用”并非后端组件故障，而是直接由被监控对象（Pod）的消失引起。输入事实未提供该 Pod 之前的生命周期日志或重启原因，因此无法判断删除行为是主动操作还是意外终止后的清理。

## 🎯 根因分析 · g3

### 因果链

```text
Pod log-observability-byconity-server-0 从 Kubernetes 集群中不存在 → Kubernetes API 返回 NotFound，且无相关 Events → 可观测性后端（Prometheus/ES/DeepFlow）因对象缺失拒绝查询 → 表现为监控数据不可用且 Pod 状态 Unknown
```

### 根因结论

已确认根因为：Pod `monitor/log-observability-byconity-server-0` 已从集群中移除（NotFound）。

这一事实直接解释了为何所有基于该实体的数据采集（指标、日志、追踪、拓扑）均返回 `NotFound` 错误。由于当前输入事实中缺乏 Pod 存活期间的详细日志（Logging 查询失败）及历史事件记录，关于 Pod 被删除的具体操作者（用户、控制器或运维脚本）以及其最终的终止状态（如 OOMKilled 或正常结束）确认为“证据不足”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 25.6s
├─ 并发证据采集: 74.2s
│  ├─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 74.2s (Evidence 65.9s, RCA 8.1s)
│  ├─ g2 monitor/local-disk-observability-byconity-server-0: 61.9s (Evidence 50.3s, RCA 11.6s)
│  └─ g3 monitor/log-observability-byconity-server-0: 62.4s (Evidence 51.8s, RCA 10.5s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
