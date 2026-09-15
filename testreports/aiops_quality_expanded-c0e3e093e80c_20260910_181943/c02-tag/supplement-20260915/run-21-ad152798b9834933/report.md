## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod workload (aiops-case-v07) 处于 Pending/ImagePullBackOff 状态，无法启动。 |
| g2 | `monitor/prometheus-observability-prometheus-0` | Unknown | Prometheus 进程因内存资源限制不足（512Mi）导致 OOMKilled，进而引发服务频繁重启与健康检查超时。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... 22m (x4 over 23m) kubelet Error: ErrImagePull` | 确认拉取失败的核心事件 |
| 2 | K8s Event | kubernetes | `Warning Failed ... 22m (x6 over 23m) kubelet Error: ImagePullBackOff` | 确认当前 Pod 状态已转为 BackOff |
| 3 | K8s Event | kubernetes | `Warning Failed ... 22m (x4 over 23m) ... rpc error: code = NotFound desc = ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` | 明确根因为目标镜像 Tag 在仓库中不存在 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 独立印证容器处于拉取镜像等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` | 排除因 OOM 或 CrashLoopBackOff 导致的重启 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` | 排除因资源限制导致无法分配启动空间 |

**证据交叉验证说明：**
1. **Kubernetes 事件与 Metrics 一致**：Event 记录了具体的 `NotFound` 错误，Metrics 则确认了容器状态稳定在 `ImagePullBackOff` 且未发生重启，佐证了问题源于镜像拉取阶段而非运行阶段（事实 #1, #3, #4）。
2. **排除其他干扰因素**：`restart_count` 为 0 且资源限制合理，排除了应用崩溃或资源争用（事实 #5, #6）。
3. **缺失维度说明**：因容器未成功启动，Logging 和 Tracing 维度无法获取，故障判定完全基于 K8s 控制层事实。

## 🎯 根因分析 · g1

### 因果链

```text
目标镜像 tag (aiops-fixture-unavailable-20260908) 在仓库中不存在 → 容器启动失败并触发 ErrImagePull 及随后的 ImagePullBackOff 状态 → Pod 持续保持 Pending 状态且无业务流量
```

### 根因结论

根因已确认：**容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在（NotFound）。**

**证据支撑：**
- **直接原因**：Kubelet 拉取镜像时返回 `rpc error: code = NotFound` 明确提示镜像 Tag 无效（事实 #3）。
- **状态印证**：Pod 状态长期处于 `ImagePullBackOff`，且 `restart_count` 为 0，排除了运行时的故障可能（事实 #2, #5）。

**局限性说明：**
- 缺少 Logging/Tracing 数据，但考虑到容器根本未启动，这些维度无实际诊断价值，现有 K8s 控制层事实已充分闭环。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `kubelet Liveness probe failed: Get "http://172.16.166.165:9090/-/healthy": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` (224次) | 证明 Prometheus 因重启/僵死导致服务频繁不可用 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory` = 512Mi | 确认 Prometheus 容器被施加了较严格的内存硬限制 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason` = "OOMKilled", `last_exit_code` = 137 | 证实 Pod 历史因内存耗尽被内核强制终止 |
| 4 | K8s State | Kubernetes | `pod.restart_count` = 2, Pod 当前 Phase = Running | 确认 Prometheus 已因 OOM 发生 2 次重启 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = 1 (label: `reason="OOMKilled"`), `kube_pod_container_status_restarts_total` = 2 | 时序数据交叉验证了 OOM 事件与重启次数 |
| 6 | Logging | Elasticsearch | `Evaluating rule failed ... many-to-many matching not allowed: matching labels must be unique on one side` | 记录 Prometheus 运行时的规则计算错误，反映其当前处于低负载或亚健康状态 |

**证据关联说明**：
证据 2、3、4、5 构成闭环：512Mi 的硬限制（#2）被突破后触发内核 OOM 终止（#3），导致 Pod 重启 2 次（#4），该历史在 Prometheus 自身的监控指标中得到确认（#5）。由于 Pod 处于频繁重启或高负载恢复期，探针请求频繁超时（#1）；日志（#6）中的匹配错误与重启现象相互印证，表明服务实例当前正在处理遗留或配置异常的规则请求。

## 🎯 根因分析 · g2

### 因果链

```text
Prometheus 内存占用持续超过 512Mi 硬限制 → Kubernetes 内核触发 OOMKilled 强制终止进程 (Exit 137) → Pod 反复重启且启动初期探针响应超时 → 健康检查频繁失败，服务可用性受损
```

### 根因结论

**已确认的根因**：`monitor/prometheus-observability-prometheus-0` 的 `prometheus` 容器被配置了 `512Mi` 的内存硬限制（`fact-0120ee7f3d2f`），该容量无法满足其实际运行需求，导致内存溢出并被内核强制杀死（`fact-143c2977b3d5`）。

这一机制直接引发了当前现象：
1.  **服务频繁重启**：Pod 已因 OOM 重启 2 次（`fact-4b6d5f1a6c8b`、`fact-d1734d354dae`）。
2.  **探针超时**：在重启和恢复过程中，Prometheus 进程无法正常响应 Liveness 和 Readiness 探针，触发 kubelet 大量超时报警（`fact-1c57360818b8`、`fact-9fae5de1d731`）。

尽管 Pod 当前状态显示为 `Running`，但由于上述 OOM 机制的反复触发，服务并未真正恢复稳定。日志中捕获的 PromQL 规则匹配错误（`fact-0518ac2fc0a7` 等）进一步表明 Prometheus 实例在恢复阶段处理能力受限或存在配置缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 34.3s
├─ 并发证据采集: 132.4s
│  ├─ g1 aiops-case-v07/workload: 55.1s (Evidence 44.3s, RCA 10.6s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 132.4s (Evidence 124.2s, RCA 8.0s)
└─ 汇总总结: 15.8s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
- **g2 monitor/prometheus-observability-prometheus-0**: pod-notready-probe-failed
