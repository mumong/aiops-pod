## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIP: 172.16.104.17/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `container.last_terminated_reason`: `Error`; `container.last_exit_code`: 2 | 确定 Pod 处于重启循环，进程因非零退出码终止 |
| 2 | K8s State | Kubernetes | `pod.condition`: `Ready`/`ContainersReady` 为 `False` (`ContainersNotReady`); `restart_count`: 13 | 确认应用当前不可用且已多次重启 |
| 3 | Logging | Elasticsearch | 聚合日志: `runtime process exiting`, HTTP status 500, path `/work`, trace_ids: `["1177dab7b64a1e5b24692ffc4375aaf6", ...]` | 提供进程主动退出的直接证据，并与 500 错误强相关 |
| 4 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 500, 源 172.16.104.21 -> 目的 172.16.104.17, trace_ids 匹配日志 (如 `1177dab7b64a1e5b24692ffc4375aaf6`) | 从流量视角确认 `/work` 接口的 500 错误并关联同一请求链 |
| 5 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 200, 源 172.16.104.21 -> 目的 172.16.104.17, trace_ids 匹配成功日志 (如 `97a75c073642b491e78d960ba0ad27a4`) | 证明应用并非永久失效，存在间歇性处理失败的情况 |
| 6 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi`; `container.resource_request.cpu`: `20m` | 确认资源限制配置，排除硬限制触发 OOM 的可能（日志显示 0M 内存消耗） |

**证据说明：**
- Kubernetes 维度的 `CrashLoopBackOff` 和 `exit_code: 2` 证实了应用异常退出（证据 1, 2）。
- Logging 中的 `runtime process exiting` 模式与 Tracing 中 `GET /work` 的 500 错误通过相同的 trace_id（如 `1177dab7b64a1e5b24692ffc4375aaf6`）直接关联，确认为同一请求触发的事件链条（证据 3, 4）。
- Tracing 中同时存在的 200 成功请求（证据 5）表明这是一个间歇性的应用内部故障，而非持续的集群网络或配置问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 → 处理 GET /work 时触发运行时异常并返回 500 → 应用执行退出操作 (exit code 2) → 容器非 OOM 重启并进入 CrashLoopBackOff
```

### 根因结论

**证据不足**。

虽然现有证据（K8s 状态、Logs、Tracing）强有力地证实了根因现象为**应用代码在处理 `/work` 接口时发生了导致进程退出的内部运行时错误（HTTP 500 + exit code 2）**，但由于日志中未记录具体的异常堆栈或错误类型（如 `NullPointerException` 等），且未收集到导致该错误的特定输入数据，目前无法从事实中进一步定位到具体的代码级缺陷或触发条件。正式 RCA 中的详细代码级原因已被配置校验拒绝发布，故本报告判定证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 14.2s
├─ 并发证据采集: 84.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 84.4s (Evidence 75.3s, RCA 8.9s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
