## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8处于Pending状态， nodeName=None，PodScheduled=False，调度器持续报告FailedScheduling |
| g2 | `monitor/prometheus-observability-prometheus-0` | Running | Prometheus Pod因OOMKilled退出并重启，且Liveness探针配置过于严格（超时3s），导致Pod长期处于未响应状态（Context deadline exceeded），进而引发Liveness Probe持续失败和大量的Prometheus Rule评估错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (fact-021ff4b47e34) | 明确调度失败的核心机制是节点亲和性不匹配，而非资源不足。 |
| 2 | K8s State | `pod.condition` | `PodScheduled` 状态为 `False`，原因为 `Unschedulable`，重复事件消息同上 (fact-16c28132cc14) | 确认 Pod 在当前时刻仍未被调度，异常持续存在。 |
| 3 | K8s Config | `container.resource_request.memory` | `8Mi` (fact-0d691e8f3a5c) | 排除低内存申请导致的调度失败可能。 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase` 值为 `1`，标签 `phase="Pending"` (fact-c8212e99abb4) | 独立指标确认 Pod 处于 Pending 阶段，与 K8s 状态一致。 |

**证据说明：**
Kubernetes 调度器事件 (证据1) 直接指出了故障原因是节点亲和性（node affinity/selector）不匹配，这与 Pod 配置（证据3）极低资源申请所隐含的资源充足场景形成对比。K8s 状态 (证据2) 与 Prometheus 监控数据 (证据4) 均从不同角度确认了该 Pod 长期停留在 Pending 状态，无调度成功迹象。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 配置了不存在的 nodeSelector 标签要求 'aiops.lab/unavailable=true' → 集群节点（master/node1/node2）缺失该Label → 调度器判定 0/3 节点匹配，触发 FailedScheduling → Pod 持续 Pending 且 nodeName 为空
```

### 根因结论
已确认的根因是 Pod 的调度约束配置错误：Pod 定义了必须匹配标签 `aiops.lab/unavailable=true` 的 nodeSelector 要求，但集群内所有可用节点均不具备该标签（证据1、2）。这导致调度器无法将 Pod 调度至任何节点，直接表现为 Pod 处于 Pending 状态且 `nodeName` 为空（证据2、4）。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-f903221a2355) | 确认内存溢出是导致容器退出的直接终止原因 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: context deadline exceeded` (fact-4eac472e68c3) | 证明 Liveness 探针持续失败，且超时机制（Client.Timeout）未等到服务恢复 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 512Mi` (fact-c069ba5e13ac) | 确认 Prometheus 容器硬内存限制，支持 OOMKilled 事实 |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory: 256Mi` (fact-2722309cd33b) | 提供资源申请限制上下文 |
| 5 | K8s State | Kubernetes | `container.last_exit_code: 137` (fact-11ad6bec79d8) | 退出码 137 再次验证了 OOMKilled (SIGKILL) 状态 |
| 6 | K8s State | Kubernetes | `container.restart_count: 2` (fact-1e68bb49a8e3) | 记录容器已被重启次数，表明故障反复触发 |
| 7 | Logging | Elasticsearch | `Evaluating rule failed ... err="found duplicate series for the match group ... many-to-many matching not allowed"` (fact-04762a6bbdfd, fact-06c1529fad21, fact-0c580f8d4570, fact-1c11d0af8922) | 揭示服务受损期间大量 PromQL 规则评估因匹配错误（Duplicate Series）失败 |
| 8 | Tracing | Deepflow | `GET /federate` duration: `3101ms - 4707ms` (fact-4797f5a524e5等) | 确认联邦接口响应延迟显著增高（3-4秒级别） |

**证据说明：**
K8s 状态与 Metrics 事实互相印证了 OOMKilled 及其引发的重启（#1, #5, #6），而 Liveness 探针的持续报错（#2）证实了容器在重启后未能及时恢复健康。日志证据（#7）与追踪证据（#8）展示了服务处于不健康状态时的具体业务表现：接口高延迟以及因查询队列受损引发的级联规则评估失败，完整还原了从资源耗尽到服务不可用及业务受损的过程。

## 🎯 根因分析 · g2

### 因果链

```text
Prometheus内存不足导致OOMKilled → 容器重启并恢复服务 → 服务恢复期间Liveness Probe超时（Context deadline exceeded） → Liveness Probe持续失败导致Pod标记为Unhealthy，并伴随大量Rule评估报错
```

### 根因结论

已确认的根因是 **Prometheus Pod 因内存不足（OOMKilled）退出并重启**，且 **Liveness 探针配置过于严格（超时 3s）**。

1.  **根本触发**：内存耗尽导致容器被强制终止（`OOMKilled`），退出码 `137` 确认了该状态（证据 #1, #5）。
2.  **恶化机制**：在容器重启或资源恢复期间，服务未能在 Liveness 探针的 3s 超时窗口内响应（`context deadline exceeded`），导致探针持续失败（证据 #2）。
3.  **业务后果**：Pod 持续被标记为不健康（Liveness Probe 失败），同时由于实例状态不稳定，Prometheus 内部发生了重复指标匹配（Duplicate Series），导致大量规则评估（如 `kubelet_pleg_relist_duration_seconds`, `CPUThrottlingHigh`）报错失败（证据 #7）。

---

## 📊 性能统计

```text
├─ 总耗时: 7.8m
├─ 问题定位: 30.7s
├─ 并发证据采集: 419.3s
│  ├─ g1 aiops-case-01/workload-68c557d875-gtzc8: 53.5s (Evidence 45.4s, RCA 8.0s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 419.3s (Evidence 409.1s, RCA 10.1s)
└─ 汇总总结: 16.1s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
- **g2 monitor/prometheus-observability-prometheus-0**: pod-notready-probe-failed
