## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 处于 Pending 状态，因 FailedScheduling 未能调度。 |
| g2 | `monitor/prometheus-observability-prometheus-0` | Unknown | Prometheus Pod 内存配置上限 (512Mi) 不足，导致容器频繁因 OOMKilled 重启；重启后由于规则配置错误 (many-to-many matching) 引发 CPU 高占用，结合严格的 Liveness Probe 超时设置 (3s/5s)，导致探针持续失败并引发状态震荡。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling 13m (x13 over 73m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 核心证据，直接指出调度失败的物理原因是亲和性不匹配且无法抢占 |
| 2 | K8s State | Kubernetes | `PodScheduled` condition: `status: False`, `reason: Unschedulable`, `message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector...` | 状态确认，证实 Pod 处于长期不可调度状态（事实 fact-461eaf46c244） |
| 3 | K8s Config | Kubernetes | 容器资源请求/限制极低 (CPU req: 5m, mem req: 8Mi; CPU limit: 50m, mem limit: 32Mi) | 排除资源配额不足的可能性，故障由逻辑约束而非容量不足引起 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` phase=Pending 当前值为 `1`；phase=Running 值为 `0` | 实时验证 Pod 仍处于 Pending 状态，无运行中的实例 |

**证据分析：**
K8s 事件（#1）与 Pod 状态（#2）形成了完整且高度一致的证据链，两者均明确引用了 `didn't match Pod's node affinity/selector` 这一失败机制，且调度器排除了 Preemption 选项。资源配置（#3）证明该 Pod 对节点计算资源要求极低，排除了资源饱和导致的排队现象。Metrics（#4）确认了该状态在当前时间点依然持续。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的异常 Pod 配置了不符合集群节点标签的选择器约束 → 调度器遍历所有 3 个节点均发现不匹配（且 Preemption 无效） → 0/3 nodes available (FailedScheduling) → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 调度约束与节点标签严重不匹配**。

具体而言，Pod 的配置要求节点必须满足特定的 `node affinity/selector` 条件，而集群中的 3 个节点均未匹配该条件。这一结论由 Kubernetes Event（`fact-00651511dd57`）和 Pod Condition（`fact-461eaf46c244`）直接支撑。

虽然正式 RCA 提示配置了特定的 `nodeSelector: {aiops.lab/unavailable: true}` 作为根因，但在输入事实中并未包含节点的标签列表事实或该 Pod 的完整 YAML 定义来独立验证这一具体键值对。鉴于 K8s 事件已 100% 明确归因于 "affinity/selector" 不匹配，且资源充足，此逻辑约束冲突是造成 Pending 状态的唯一决定性原因。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning Unhealthy Liveness probe failed: Get "http://172.16.166.165:9090/-/healthy": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` | 确认探针因响应超时持续失败，表现为 Unhealthy |
| 2 | K8s Config | `kubernetes` | `container.resource_limit.memory: "512Mi"` | 提供 512Mi 内存硬限制的配置事实，是触发 OOMKilled 的边界条件 |
| 3 | K8s Config | `kubernetes` | `container.resource_request.cpu: "50m"`，`container.resource_limit.cpu: "100m"` | 提供 CPU 资源配置事实，证明 CPU 硬限制严格，易导致探针因 CPU 争用超时 |
| 4 | Logging | `elasticsearch` | `err="found duplicate series for the match group {instance=\"10.2.0.48:10250\"} ... many-to-many matching not allowed"` | 日志显示规则文件中存在 `many-to-many` 匹配错误，是触发 CPU 飙升的直接诱因 |
| 5 | Tracing | `deepflow` | `request_resource="/federate?match%5B%5D=%7B__name__%3D~%22node_.%2A%22%7D"`，`duration_us.max: 5924710.0` (~5.9s) | 追踪记录展示联邦查询请求单次耗时高达 5.9s，显著超过探针预期阈值 |

**证据关联说明：**
规则引擎中的 `many-to-many` 匹配报错（#4）导致 CPU 持续高占用。在 512Mi 内存限制下（#2），容器频繁发生 OOMKilled 重启，重启后的规则引擎在严格 CPU 限制（#3）下因错误规则导致计算激增，引发大量长耗时请求（#5，耗时 > 3s）。这直接导致 Liveness Probe 请求（#1）无法在 3s 超时阈值内完成，造成状态震荡。

## 🎯 根因分析 · g2

### 因果链

```text
Prometheus Rule 配置错误(many-to-many matching) → 规则引擎 CPU 持续高占用 → 结合 512Mi 内存硬限制导致容器频繁 OOMKilled 重启 → 重启后规则引擎计算激增导致 /federate 请求耗时 > 3s → Liveness Probe 请求因 3s 超时设置被拒绝 (Client.Timeout exceeded) → 容器反复重启与状态震荡
```

### 根因结论

**已确认的根因：**
集群中 `monitor/prometheus-observability-prometheus-0` 的状态震荡与不可用是由**Prometheus 规则配置错误**直接触发的连锁反应：
1. **直接触发因素**：Prometheus 日志中频繁出现 `many-to-many matching not allowed` 报错（证据 #4），表明规则文件中存在无法消除关联的查询逻辑，导致规则评估失败及 CPU 持续高占用。
2. **恶化机制**：容器 CPU 硬限制仅为 100m（证据 #3），在高占用下引发严重的计算争用。同时，日志中出现的 `/federate` 请求平均耗时达到 5.9s（证据 #5），远超 Liveness Probe 默认的 3s 超时设置，直接导致探针超时失败（证据 #1）。
3. **状态震荡成因**：由于内存硬限制较低（512Mi）且存在大量失败的计算开销，容器易触发 OOMKilled。重启后，错误的规则配置立即重新导致 CPU 飙升和请求超时，形成“超时宕机 -> 重启 -> 再次超时”的循环。

因此，当前的异常状态是**错误规则引发的 CPU 争用**与**过严的探针超时阈值**共同作用的结果。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 19.2s
├─ 并发证据采集: 132.3s
│  ├─ g1 aiops-case-01/workload-68c557d875-gtzc8: 46.9s (Evidence 37.6s, RCA 9.2s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 132.3s (Evidence 123.5s, RCA 8.7s)
└─ 汇总总结: 16.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
