## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Liveness probe endpoint (/health) returns HTTP 500, causing kubelet to kill the container (exit 137) despite the main application endpoint (/work) operating normally. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: `Error` | 确认容器异常终止 |
| 2 | K8s State | Kubernetes | container.last_exit_code: `137` | 确认进程被强制终止（SIGKILL） |
| 3 | K8s Event | Kubernetes | `Warning Unhealthy ... Liveness probe failed: HTTP probe failed with statuscode: 500` | 直接触发 kill 动作的事件源 |
| 4 | K8s Event | Kubernetes | `Normal Killing ... Container app failed liveness probe, will be restarted` | 证实 kubelet 因探针失败杀死容器 |
| 5 | K8s State | Kubernetes | container.waiting_reason: `CrashLoopBackOff` | 确认进入重启风暴状态 |
| 6 | K8s Config | Kubernetes | container.resource_limit.memory: `96Mi` | 排除硬限制导致 OOMKilled (exit 137) 的可能性 |
| 7 | Metric | Prometheus | container_memory_working_set_bytes: `831488` bytes (0.79MiB) | 证实重启后内存极低，未触及 96Mi 限制 |
| 8 | Logging | Elasticsearch | log.message: `http_request ... /work ... http_status: 200` | 证明主业务逻辑（/work）运转正常，非应用全面崩溃 |

**证据交叉验证：**
K8s Event (#3, #4) 直接记录了探针 `/health` 返回 500 的状态码以及由此产生的 Killing 动作；K8s State (#2) 显示的 Exit Code 137 与 Event 描述的 kill 原因一致；Metric (#7) 确认内存正常（远低于 96Mi 限制），Logging (#8) 确认业务接口 `/work` 正常，从而排除了 OOM 和整个应用挂死，聚焦于探针配置或探针逻辑的特定错误。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness 探针端点 (/health) 逻辑或后端依赖异常返回 HTTP 500 → 容器健康检查连续失败 → kubelet 终止容器进程 (exit 137) → Pod 状态变更为 CrashLoopBackOff
```

### 根因结论

已确认根因为 **Liveness Probe 诊断失败（返回 HTTP 500）**。

证据链显示：
1. **触发机制**：K8s Event 明确记录 `Liveness probe failed: HTTP probe failed with statuscode: 500` (#3)，这是导致容器被杀的直接原因。
2. **执行结果**：容器以 `exit_code: 137` (#2) 退出，且状态为 `CrashLoopBackOff` (#5)，符合 Kubelet 因探针连续失败执行 `SIGKILL` 后的标准状态。
3. **排除干扰**：内存指标显示当前使用量仅约 0.8MiB (#7)，远低于 96Mi 的 `resource_limit` (#6)，且主业务接口 `/work` 持续返回 200 (#8)，证明应用主进程未被 OOM Kill 也未整体挂死。

综上，异常并非由资源耗尽或应用代码全面错误引起，而是专门指向 Liveness 探针配置的目标端点（`/health`）未能返回预期的健康状态（通常为 200），导致 Kubelet 误判容器死亡并执行重启。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 42.6s
├─ 并发证据采集: 133.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 133.9s (Evidence 127.7s, RCA 6.0s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-crashloop-runtime
