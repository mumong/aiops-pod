## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，且 RestartCount 为 12。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `phase=CrashLoopBackOff`, `restart=12` | 确证容器主进程退出后处于重启失败或循环重启状态。 |
| 2 | K8s Event | Metrics | `status_reason=CrashLoopBackOff` / `last_terminated_reason=Error` (fact-11db9f56a38f, fact-2c780881efec) | 确认容器最近一次终止原因为 Error，且当前因重启策略进入 BackOff。 |
| 3 | Logging | ES Log | `[Error]` `http_request` `message="runtime process exiting"` `http_status=500` `path="/work"` (fact-7376f1603c05 等) | 提供关键证据：应用进程在响应 HTTP 500 后主动触发退出行为。 |
| 4 | Tracing | Tempo/Deepflow | `GET /work` `http.response.status_code=200` `trace=153a...` (fact-49798e4ec67a)；`GET /work` `response_code=500` `trace=658a...` (fact-24e9f65d195a) | 证明应用能正常响应请求，但存在引发 500 响应的失败链路，且该 500 与日志中的退出直接相关。 |
| 5 | Metric | K8s State | `phase=Running` (kube-state-metrics) | 排除节点级别整体故障，确证异常仅发生在目标 Pod。 |

**证据关联分析：**
*   **时序与因果印证**：Logging 中的 `http_status: 500` (fact-7376f1603c05) 与 Tracing 中 `response_code: 500` (fact-24e9f65d195a) 相互印证，展示了具体的失败请求；Logging 紧接着记录 `runtime process exiting` (fact-7376f1603c05 等)，表明进程在收到或返回 500 错误后终止。
*   **生命周期闭环**：Metrics 显示的 `last_terminated_reason=Error` (fact-2c780881efec) 是日志中“进程退出”的直接后果，而 `restart=12` 且处于 `CrashLoopBackOff` 则确认了 kubelet 试图重启该异常退出进程但持续失败或进入退避循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码/逻辑在 /work 路径引发异常 → 返回 HTTP 500 错误 → 主进程执行退出逻辑 (runtime process exiting) → 容器退出并被标记 Error → K8s 重启策略触发循环重启 (CrashLoopBackOff)
```

### 根因结论

已确认根因为：**应用主进程在处理 HTTP `/work` 请求返回 500 错误后，主动终止了运行进程。**

*   **直接原因引用**：Elasticsearch 日志清晰记录了 `message="runtime process exiting"` 伴随 `http_status=500` (证据 3, 4)；Prometheus 指标确认了容器以 Error 状态终止并进入重启循环 (证据 1, 2)。
*   **现象解释**：Pod 处于 `CrashLoopBackOff` 且 RestartCount 为 12，是因为 K8s 检测到主进程 (PID 1) 异常退出后尝试重启，但应用逻辑导致其再次触发退出，最终因重启间隔超过退避上限而锁定状态。
*   **未确认事项**：无法从当前数据确定 500 错误的具体业务逻辑原因，也无法判断该“执行后即退出”的行为是否符合单任务处理模式的业务预期。

---

## 📊 性能统计

```text
├─ 总耗时: 3.5m
├─ 问题定位: 23.5s
├─ 并发证据采集: 175.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 175.9s (Evidence 166.2s, RCA 9.5s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
