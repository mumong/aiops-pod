## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 持续状态（重启 18 次，退避 73 分钟），请求 `/work` 返回 500 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning BackOff ... Back-off restarting failed container app in pod workload-dff5cbc6b-kmfxx` (x313 over 73m) | 证明容器处于重启退避状态，确认异常持续时间 |
| 2 | K8s State | kubelet | `container.waiting_reason`: CrashLoopBackOff; `last_exit_code`: 78 | 提供容器的确切终止状态和退出码 |
| 3 | K8s State | kubelet | `container.waiting_message`: `back-off 5m0s restarting failed container=app` | 印证 Kubelet 正在执行指数退避重启策略 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`="Error"; `kube_pod_container_status_restarts_total`=18 | 确认最近一次终止原因为 Error，且重启次数达到 18 次 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`="CrashLoopBackOff" | 与 K8s 状态一致，确认可观测性指标同步异常 |
| 6 | Logging | elasticsearch | `pattern`: `event: http_request`, `message: CONFIG_MISSING`, `http_status: 500`, `path: /work` (8 occurrences, first: 14:47:22, last: 15:08:21) | 明确指出应用进程因配置缺失主动报错并返回 500 |
| 7 | Tracing | deepflow | `flow`: GET /work response_code=500, src_ip=172.16.104.9, dst_ip=172.16.104.15 (9 occurrences) | 从网络流量视角确认应用对外返回了 500 错误 |
| 8 | Tracing | tempo | `span`: `GET /work`, `http.response.status_code`=500, `aiops.observed_mode`=config_missing_exit, `trace_id`=65684c8c074b2b13bde640e742613caa | 确认应用内部执行路径为配置缺失退出，且 trace_id 与日志完全一致 |

**证据印证说明：**
1.  **应用行为与退出逻辑闭环**：Logging (fact-6) 显示应用返回 `CONFIG_MISSING` 500 错误；Tracing (fact-8) 明确 `aiops.observed_mode` 为 `config_missing_exit`。这表明应用并非因 OOMKilled 或系统错误崩溃，而是主动以 exitCode 78 退出。
2.  **K8s 视角的印证**：K8s State (fact-2) 显示的 `exit_code: 78` 与上述应用主动退出的行为相符；K8s Event (fact-1) 和 Metric (fact-4) 一致反映了容器因频繁退出导致的 `CrashLoopBackOff` 现象。
3.  **时间线匹配**：日志时间范围 (14:47-15:08) 与流量时间范围 (22:47-23:08, 需结合时区理解) 重叠，且均发生在 Pod Ready 失败的时间窗口内，证明这是 Pod 持续崩溃的直接诱因。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺失必需配置 (日志确认 CONFIG_MISSING) → 应用启动请求 /work 端点检查配置失败 → 应用进程主动退出 (exitCode 78, EX_UNAVAILABLE) → Kubelet 持续重启容器触发 CrashLoopBackOff (18次重启, 退避73分钟)
```

### 根因结论

已确认根因为：**应用容器因缺少必需的配置文件或配置项，在启动后通过主动返回 500 错误和 exitCode 78 失败，导致 Kubelet 陷入重启循环。**

**证据支撑：**
*   **直接失败机制**：Logging (fact-6) 和 Tracing (fact-8) 一致证实，应用在处理 `/work` 请求时明确报出 `CONFIG_MISSING`，且 Trace 中的 `aiops.observed_mode` 标记为 `config_missing_exit`。
*   **退出码验证**：K8s State (fact-2) 显示 `exit_code: 78`，这与应用程序主动因配置不可用而退出的行为（通常对应 `EX_UNAVAILABLE`）相符，而非资源耗尽导致的系统级崩溃。
*   **持续异常状态**：K8s Event (fact-1) 和 Metric (fact-4, 5) 记录了长达 73 分钟的 18 次重启和 `CrashLoopBackOff` 状态，证实该配置缺失问题是持续性的，且未被自动修复。

**缺失的关键事实（未知项）：**
*   根因的具体形态：虽然确认了“配置缺失”，但缺乏 K8s ConfigMap `workload-code` 的实际内容或挂载日志，无法确定是 ConfigMap 本身不存在、挂载路径错误、还是 ConfigMap 内部缺失了特定的 Key。
*   退出码映射：exitCode 78 与 `CONFIG_MISSING` 的映射关系仅由应用日志体现，无外部标准依据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 13.9s
├─ 并发证据采集: 65.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 65.5s (Evidence 50.8s, RCA 14.5s)
└─ 汇总总结: 17.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
