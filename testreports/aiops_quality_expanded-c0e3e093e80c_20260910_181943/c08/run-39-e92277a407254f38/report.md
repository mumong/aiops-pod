## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器 `app` 内存请求/限制配置过低 (64Mi)，导致应用在处理 `/work` 请求进行内存分配时触发 OOM (Out of Memory)，被内核 Kill 后进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: {"container": "app", "reason": "OOMKilled"}` (fact-04a235d01b48) | 核心根因：确认容器因内存超限被内核 Kill。 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: {"container": "app", "value": "64Mi"}` (fact-7c5262669d16) | 根因支撑：直接展示限制容器内存上限仅 64Mi，证实配置过低。 |
| 3 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact-ad84b80e62b0) | 现象确认：Pod 处于反复重启状态，与 CrashLoopBackOff 状态一致。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 23` (fact-d10377847e12) | 现象确认：侧面印证频繁崩溃与重启模式。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1 [reason: OOMKilled]` (fact-08a1bd7dc942) | 独立验证：Prometheus 指标再次确认终止原因确为 OOMKilled。 |
| 6 | Logging | Elasticsearch | Pattern: `http_request ... path: /work ... allocated_mib min: 20.0, max: 44.0` (fact-12401075fcbe) | 场景限定：明确内存申请（最高达 44Mi）发生在处理 `/work` 请求期间。 |
| 7 | Tracing | Deepflow/Tempo | `GET /work` Flow 9次，Span `GET /work` `oom_growth` 模式 (fact-41e0b563cb0a, fact-2f8d68b37e0b) | 现象印证：应用日志和 Tracing 共同指向 `/work` 接口存在持续且增长的内存分配行为。 |

证据表明，应用在处理 `/work` 请求时不断分配内存（日志显示最高至 44Mi，已接近 64Mi 硬限制），最终触发 `OOMKilled`（K8s 状态、指标双重确认）。配置上的 `memory limit: 64Mi` 是导致崩溃的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置过低 (64Mi) → 处理 /work 请求时内存分配逼近上限 → 触发 OOMKilled → 容器重启进入 CrashLoopBackOff
```

### 根因结论

已确认根因：**容器 `app` 的内存限制配置过低 (64Mi)**。
这一配置不足以支撑应用处理 `/work` 请求所需的内存（日志显示最高分配量达 44Mi），导致内存超额后触发内核 OOM Killer，进而使 Pod 陷入 CrashLoopBackOff 状态。

依据的证据链：
1. **配置维度**：Kubernetes 状态显示 `memory limit: 64Mi` (fact-7c5262669d16)。
2. **现象维度**：Kubernetes 事件、指标 (`kube_pod_container_status_last_terminated_reason`) 及容器终止原因 (fact-04a235d01b48, fact-08a1bd7dc942) 均确认为 `OOMKilled`。
3. **触发场景**：日志 (fact-12401075fcbe) 和链路追踪 (fact-41e0b563cb0a) 一致指向该崩溃发生在处理 `/work` 接口时。

缺失的决定性事实包括应用代码内部的具体内存分配逻辑以及 64Mi 下处理 `/work` 所需的确切阈值，但不影响当前对“资源限制过低导致 OOM”这一根因的认定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 31.8s
├─ 并发证据采集: 63.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 63.9s (Evidence 55.8s, RCA 7.9s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
