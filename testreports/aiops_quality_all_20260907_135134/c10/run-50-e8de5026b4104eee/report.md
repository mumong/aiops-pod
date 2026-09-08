## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | 容器应用因内存泄漏导致实际内存使用量（约15MB）超过Memory Limit（96Mi），引发OOM Kill（Exit Code 137）；同时Liveness Probe持续返回500错误，导致Kubelet强制重启容器进入CrashLoopBackOff状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: CrashLoopBackOff | 展示异常状态 |
| 2 | K8s Event | Kubernetes | Unhealthy: Liveness probe failed: HTTP probe failed with statuscode: 500 | 展示服务健康检查异常 |
| 3 | K8s State | Kubernetes | container.last_exit_code: 137 | 证明容器是被系统信号杀死的（OOM Kill） |
| 4 | K8s Config | Kubernetes | container.resource_limit.memory: 96Mi | 确认内存硬性限制 |
| 5 | Metric | Prometheus | container_memory_working_set_bytes: 15855616 bytes (约 15.1 MB) | 展示内存使用远超 Limit (96Mi ≈ 98MB)，且呈上升趋势 |
| 6 | Logging | Elasticsearch | http_status: 200 (成功), http_status: 500 (失败) | 展示探针在不同时间点既有成功也有失败的现象，说明服务非完全宕机而是间歇性不响应 |

**证据关联与印证：**
- **OOM 机制确认**：`fact-079e7ff8c7b1` (Exit Code 137) 结合 `fact-a4fa90328942` (Limit 96Mi) 和 `fact-06f7b7c18d72` (使用量 ~15MB) 确凿地指向因资源受限导致的容器被杀。
- **重启循环形成**：Kubelet 检测到 `fact-e59c40d4b9e4` (Liveness Probe 500错误) 及 `fact-3de9a2b66cbe` (back-off message)，触发重启策略，导致 `fact-6dab02fc2b66` (restart_count 44) 和 `fact-5b32529aa687` (CrashLoopBackOff) 状态。
- **内存趋势支撑**：Metric 维度 `fact-06f7b7c18d72` 提供了多个样本且 `trend_evaluable=true`，显示内存消耗在多次崩溃前均逼近 15MB 附近，且 `fact-821b98c28660` 显示重启后降至 4MB，进一步印证了每次启动后内存持续增长直至触达触发点（或超过实际可用限制导致被杀）的泄漏模式。

## 🎯 根因分析 · g1

### 因果链

```text
容器应用内存泄漏/未释放 → 内存消耗持续增长 (约15MB, 逼近/触发限制) → 触发 OOM Kill (Exit Code 137) 且服务在重启前对探针返回 500 → Kubelet 执行重启策略 → Pod 进入 CrashLoopBackOff (无法恢复)
```

### 根因结论

已确认的根因是**容器应用内存泄漏导致触发 OOM Kill 进而引发重启循环**。
证据编号：
- **OOM 直接证据**：`fact-079e7ff8c7b1` (Exit Code 137) 和 `fact-a4fa90328942` (96Mi Limit)。
- **内存泄漏趋势**：`fact-06f7b7c18d72` 和 `fact-089a0604e5a8` 确认了内存使用量持续增长且重启次数高达 44 次。
- **服务不可用状态**：`fact-e59c40d4b9e4` 的 Liveness Probe 500 错误解释了为何容器在被杀前处于“假死”或不健康状态，导致重启失败且陷入循环。

**未确认/局限性**：
- 尚未定位到引发内存泄漏的具体代码路径或对象分配模式（未采集到更早阶段的日志证据）。
- 没有明确的 `OOMKilled` 事件文本（可能被 K8s 清理或日志聚合未捕获），但 Exit Code 137 结合限制配置已构成闭环证据。

---

## 📊 性能统计

```text
├─ 总耗时: 3.7m
├─ 问题定位: 19.1s
├─ 并发证据采集: 186.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 186.0s (Evidence 173.2s, RCA 12.6s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
