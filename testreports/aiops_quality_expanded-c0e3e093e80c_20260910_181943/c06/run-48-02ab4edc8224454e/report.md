## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用进程在 /work 端点执行时发生内部运行时错误导致退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` status: `CrashLoopBackOff`；Exit Code: `2` | 明确应用进程以错误码 2 异常终止，处于频繁重启状态 |
| 2 | K8s State | Kubernetes | `BackOff` Event：`Back-off restarting failed container app` (2m34s, x497 over 112m) | 佐证容器频繁崩溃并进入 BackOff 延迟重启阶段，异常持续约 2 小时 |
| 3 | K8s Config | Kubernetes | Resource Request: Memory `24Mi` / CPU `20m`；Limit: Memory `96Mi` / CPU `200m` | 排除资源限制导致的 OOMKilled，确认容器拥有相对充足的内存/计算资源 |
| 4 | Logging | Elasticsearch | Pattern: `runtime process exiting` (Status 500, path `/work`) 4 次 (19:56 - 20:22)；`allocated_mib`: `0` | 直接记录应用运行时崩溃事件，未观察到内存分配异常增长，指向内部逻辑或运行时错误 |
| 5 | Tracing | Deepflow | HTTP Flow: `GET /work` `Response Code: 500` 3 次 (04:01 - 04:17) | 从网络流量维度证实 `/work` 端点在服务侧返回 500 错误，与日志记录对应 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `26` | 量化容器重启次数，确保持续性故障特征 |

**证据说明**：
Kubernetes 状态的 `Exit Code: 2` 结合 Log/Tracing 中明确的 `runtime process exiting` (500 错误)，共同指向应用内部处理 `/work` 请求时发生非系统级（如未越限）的运行错误。Metrics 和 Events 确认了该错误触发了频繁的重启机制，而配置数据显示资源充足，排除了资源耗尽原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部运行时错误 → /work 端点返回 500 并触发进程退出 (Exit 2) → K8s 触发自动重启 → CrashLoopBackOff 循环
```

### 根因结论

**已确认的根因**：应用进程在处理 `GET /work` 请求时发生内部运行时错误（`runtime process exiting`），导致进程以非零状态码退出并触发 K8s 重启机制。

**证据引用**：
- **运行时错误**：日志明确记录 `event: http_request, message: runtime process exiting, http_status: 500` (事实 4)；
- **网络侧表现**：流量记录显示 `response_code: 500` (事实 5)；
- **系统侧表现**：容器 Exit Code 为 `2`，状态处于 `CrashLoopBackOff` (事实 1)；
- **排他性确认**：资源 Request/Limit 充足 (事实 3) 且日志中 `allocated_mib` 为 `0`，排除资源超限导致的系统干预退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.0s
├─ 并发证据采集: 45.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 45.2s (Evidence 37.3s, RCA 7.8s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled
