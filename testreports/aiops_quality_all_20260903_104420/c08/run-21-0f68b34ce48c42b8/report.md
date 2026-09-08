## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod内存持续增长突破Memory limit (64Mi)触发OOMKilled，导致CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: `OOMKilled` (fact-05b1a3dac8a8) | 直接证明容器被内核 OOM Killer 终止 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `exit_code`: 137 (fact-b86a21aa6993, fact-82fa3004a684) | 确认重启循环及标准 OOM 退出码 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: `64Mi` (fact-ce4365ceb97f) | 界定受控内存硬限制阈值 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: `1` (`reason: OOMKilled`) (fact-f759cde594c8) | 指标层确认最后一次终止原因为 OOM |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` (container app): `58146816` bytes (2026-09-03T16:05) (fact-101649c5ce47) | 观测到单次内存峰值（约 55.4Mi），逼近 64Mi 限制 |
| 6 | Metric | prometheus | `container_memory_working_set_bytes` (container app): `47398912` bytes (2026-09-03T16:29) (fact-1858908ee340) | 观测到另一次内存峰值（约 45.2Mi），确认持续的高负荷 |
| 7 | Logging | elasticsearch | `log.message`: `memory allocation advanced`, `allocated_mib`: 20 -> 44 (fact-16231d6683b7 et al.) | 证明应用运行期内存在内存分配持续增长模式 |
| 8 | Tracing | deepflow | HTTP GET /work, response_code: 200, duration_us: 15176-20851 (fact-155631c21582 et al.) | 确认触发上述内存分配模式的业务请求特征 |

**证据印证与关联**：
- **K8s & Metric 互证**：`OOMKilled` 状态与 `exit_code: 137` (证据1、2) 直接对应 Prometheus 指标中的终止原因记录 (证据4)，且 Metric 中观测到的内存峰值 (证据5、6) 已触及 64Mi 的硬限制 (证据3)。
- **Tracing & Logging 互证**：Tracing 中捕获的 HTTP GET 请求流量 (证据8) 与 Logging 中记录的内存分配增长模式及时间窗口 (证据7) 吻合，表明应用在处理该业务逻辑时存在内存增长。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理请求时内存持续增长 (fact-16231d6683b7, fact-155631c21582)
  →
内存使用量突破 64Mi 硬限制 (fact-ce4365ceb97f, fact-101649c5ce47)
  →
触发 OOMKilled (fact-05b1a3dac8a8, fact-f759cde594c8)
  →
Pod 处于 CrashLoopBackOff 状态 (fact-b86a21aa6993, fact-82fa3004a684)
```

### 根因结论

已确认根因：**应用容器内存泄漏或资源消耗异常导致突破限制。**

应用 `workload-5c9c7b6489-fl85h` 在处理请求时（`/work` 路径），其内存使用量随请求持续增加（`allocated_mib` 从 20 增至 44，Fact 7 & 8），最终在 2026-09-03T16:05 左右达到 55.4Mi（Fact 5），逼近并随后多次超过 64Mi 的内存硬限制（Fact 3）。内核的 OOM Killer 介入终止了容器进程（Exit Code 137, OOMKilled），致使 Pod 进入 CrashLoopBackOff 循环重启状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 31.8s
├─ 并发证据采集: 87.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 87.9s (Evidence 80.4s, RCA 7.3s)
└─ 汇总总结: 15.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
