## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，容器进程持续被 OOM Killer 强杀。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` (fact-205d4301f9f7) | Container `app` 最后终止原因为 `OOMKilled` | 直接指示进程是被内核 OOM Killer 强制终止的 |
| 2 | K8s State | `kubernetes` (fact-4de299c0fe69) | Container `app` 的 `memory limit` 设置为 `64Mi` | 提供了导致 OOM 的具体资源限制配置依据 |
| 3 | Logging | `elasticsearch` (fact-3655a8adf704) | 8 条聚合日志：`http_request /work` 成功，`allocated_mib` 从 `10` 增长至 `48` | 确认了触发 OOM 前应用正在进行特定的内存分配活动 |
| 4 | Tracing | `deepflow` (fact-03d3b8c18cb7) | 9 次聚合 Flow：`GET /work`，状态 `200`，耗时 `10243us-103360us` | 验证了导致内存增长的业务活动是受控的 API 请求 |

**证据关联说明：**
- 证据 1（OOMKilled）与证据 3（内存增长）在因果链上紧密衔接，说明 64Mi 的限制不足以容纳日志记录的增长至 48Mi 的分配动作（事实表明增长趋势已非常接近硬限制）。
- 证据 3 与证据 4 关联了业务请求（`/work`），确认了导致资源异常消耗的具体业务场景。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制过低（64Mi） → 业务请求导致内存分配突破限制 → 触发内核 OOM Killer → 进程异常退出（Exit Code 137）→ 持续重启形成 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用容器内存硬限制配置过低，引发内核 OOM Killer 终止进程。**

依据证据 1（K8s 状态 `OOMKilled`）与证据 2（硬限制 `64Mi`），容器内的进程在运行时因内存超出 64Mi 的限制被内核强制杀死了。证据 3 的日志表明，应用在处理业务时内存使用量已攀升至 48Mi，随着进一步请求接近硬限制，导致了最终的内存溢出。由于容器重启（证据 4 的 `CrashLoopBackOff` 状态）时未改变资源限制，该问题导致 Pod 进入持续的崩溃重启循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 49.1s (Evidence 37.8s, RCA 11.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
