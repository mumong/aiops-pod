## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod 内存限制（64Mi）设置过低，导致容器在处理 /work 请求分配内存时触发 OOMKilled (Exit Code 137)，进而引发持续重启和 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-8ef0991d1edc) | 确认容器因内存耗尽被内核强制终止 |
| 2 | K8s Event | Kubernetes | `Exit Code: 137` (fact-d026bb32e91a) | 确认终止状态符合信号 9 特征（OOMKilled） |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-45becfea05b5) | 提供资源边界配置，证实限制值极低 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: CrashLoopBackOff` (fact-15021bf1c3e5) | 指标层面确认工作负载处于持续重启状态 |
| 5 | Logging | Elasticsearch | `/work` 请求日志内存分配增长：`allocated_mib` 从 16 增长至 46 (fact-07b8092d4d39 聚合) | 展示业务请求在处理过程中内存分配量持续上升，逼近 64Mi 上限 |
| 6 | Tracing | Deepflow | `GET /work` 请求返回 `200`，耗时 16594μs-36230μs (fact-87ac5b5880c7 聚合) | 流量层面显示请求正常进入并处理，验证了内存分配与请求服务的关联 |

**证据说明：**
- Kubernetes 状态（#1, #2）确认了“容器因 OOM 退出”这一核心事实，与 Metric 状态（#4）完全一致。
- 配置（#3）提供了 64Mi 的硬限制。
- 日志（#5）与 Tracing（#6）共同证实了：在正常处理 `/work` 请求时，内存分配量（最高达 46Mi）接近 64Mi 的剩余缓冲，这是导致频繁触发 OOMKilled 的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存资源限制设置过低 (64Mi) → 请求处理期间内存分配逼近限制 (日志显示分配量达 46Mi) → 触发内核 OOM Killer 强制终止容器 (Exit Code 137) → Kubernetes 持续重试导致 CrashLoopBackOff
```

### 根因结论

已确认根因为：Pod `aiops-case-08/workload-5c9c7b6489-fl85h` 的 `app` 容器内存限制（`memory limit`）配置为 64Mi，而该限制值过低，无法承载业务请求 `/work` 处理时的内存分配需求。

具体证据如下：
1. **终止原因确认**：Kubernetes 事件显示容器最后终止原因为 `OOMKilled` 且退出码为 `137`（#1, #2）。
2. **配置与现象的矛盾**：容器内存硬限制仅为 64Mi（#3），但日志记录显示在处理 `/work` 请求时，内存分配量从 16Mi 增长至 46Mi（#5）。
3. **直接机制**：请求处理过程中的内存分配峰值接近 64Mi 的限制阈值，触发了内核的内存保护机制，导致容器被系统强制杀死并重启（#4, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.8s
├─ 并发证据采集: 69.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 69.4s (Evidence 62.6s, RCA 6.7s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
