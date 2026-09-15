## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod spec 中 Readiness Probe 配置的监听端口(18081)与应用程序实际启动端口(18080)不一致，导致探针请求被拒绝，Pod 持续处于 NotReady 状态。 |
| g2 | `monitor/prometheus-observability-prometheus-0` | Unknown | Pod内存限制设置过低（512Mi）导致Prometheus进程频繁OOMKilled重启，且存在多对多匹配（many-to-many）配置错误阻碍规则评估，造成服务不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady=False`, `ContainersNotReady`, `containers with unready status: [app]` (fact-65b8b262fef4) | 证明容器已启动但未能通过就绪检查，符合端口不匹配导致的拒绝现象 |
| 2 | K8s State | kubernetes | `Pod Scheduled=True`, `Initialized=True`, `RestartCount=0` (fact-11bcff66c933, fact-ca50468fd935, fact-ccdbb401cd4a) | 排除集群调度或容器启动崩溃问题，将异常缩小至应用生命周期阶段 |
| 3 | Logging | elasticsearch | `listening on 18080` (fact-5dd54cd9b22b) | 提供应用实际监听端口 (18080) 的事实依据，用于对比探针配置 |
| 4 | K8s Config | kubernetes | `Readiness Probe targetPort=18081` (来自 diagnosis) | 提供异常的根本原因配置，证实探针请求将发送至未监听的端口，导致连接被拒 |

**证据小结：**
Kubernetes 状态与日志证据高度一致。状态数据证明容器已正常运行（无重启），但处于 NotReady 状态；日志确认应用监听 18080 端口；诊断数据揭示探针配置了错误的 18081 端口。三者共同证实探针因端口不匹配导致请求被拒绝。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置错误（端口 18081）→ Readiness Probe 连接被拒绝 → 应用实际端口(18080)未收到请求 → Pod 持续处于 NotReady 状态
```

### 根因结论

已确认根因为 **Pod 规格中 Readiness Probe 配置的监听端口 (18081) 与应用程序实际启动端口 (18080) 不一致**。

该配置错误导致就绪探针的请求被发送到不存在的端口，引发连接拒绝。Kubernetes 持续判定容器未就绪（证据 #1），尽管容器本身已正常启动并监听在 18080 端口（证据 #2, #3）。

**未确认项：** 探针配置中的具体路径 `/ready` 是否也需要调整，或是否存在该端点（证据不足）。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `prometheus` 最后终止原因: `OOMKilled` (fact-da2d273a214a) | 确认内存超限导致进程崩溃的直接事实 |
| 2 | K8s Config | Kubernetes | 容器 `prometheus` 内存限制 `resource_limit.memory`: `512Mi` (fact-adefaf4e90bd) | 确认触发 OOM 的资源配置边界 |
| 3 | K8s Event | Kubernetes | Liveness Probe 失败: `context deadline exceeded` (fact-736024661f30) | 说明 OOM 导致进程无法响应健康检查 |
| 4 | K8s State | Kubernetes | Pod `Status`: `Running`, `restart_count`: 2 (fact-877a70393601, fact-d4ff8ef85795) | 证实故障处于持续发生和重启中 |
| 5 | Logging | Elasticsearch | 规则评估失败: `many-to-many matching not allowed` 报错 (fact-071572a32530) | 证实配置错误导致规则无法执行 |
| 6 | Logging | Elasticsearch | 报错涉及 `group_left` 匹配重复 series `10.2.0.48:10250` (fact-071572a32530, fact-0ca0369f68c7) | 定位具体的 PromQL 语法冲突 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 显示 `OOMKilled` (fact-da5af99b4c5f) | 独立于 K8s State 的指标侧佐证 |

证据链说明：
- 维度间高度一致：Kubernetes 事件显示探针因超时失败（#3），同时状态数据（#1, #4）和 Metrics（#7）均确认 OOMKilled 原因。
- 配置关联性强：日志（#5）报告的 many-to-many 匹配错误独立于 OOM 崩溃，但属于同一组件（Prometheus）的配置缺陷。
- 资源限制确定：Kubernetes 配置（#2）明确给出了 512Mi 的限制值，是支撑 OOM 结论的关键依据。

## 🎯 根因分析 · g2

### 因果链

```text
内存限制过低(512Mi)且存在many-to-many匹配配置错误 → Prometheus进程因内存耗尽被OOMKilled及健康检查超时 → Pod频繁重启、规则评估失败 → 服务不可用
```

### 根因结论

已确认的根因包括两个维度的配置与资源问题：
1. **资源限制不当**：容器 `prometheus` 的内存限制被硬设置为 `512Mi`，导致进程因内存耗尽频繁触发 OOMKilled 并被终止（证据 #1, #2, #7）。这直接引发了 Liveness Probe 的超时失败（证据 #3）和 Pod 的持续重启（证据 #4）。
2. **规则配置错误**：Prometheus 的 `kubelet.rules` 中存在 `group_left` 导致的 `many-to-many` 匹配冲突，且匹配标签 `instance` 对应的 Series 不唯一（证据 #5, #6），致使相关记录规则（如 `node_quantile`）和告警规则（如 `KubeletPodStartUpLatencyHigh`）评估失败。

以上两类证据互相印证了 `monitor/prometheus-observability-prometheus-0` 实例处于服务不可用的状态。

---

## 📊 性能统计

```text
├─ 总耗时: 10.4m
├─ 问题定位: 28.9s
├─ 并发证据采集: 581.7s
│  ├─ g1 aiops-case-v16/workload: 49.6s (Evidence 38.2s, RCA 11.3s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 581.7s (Evidence 573.9s, RCA 7.5s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **未归属 lane**: pod-notready-probe-failed
