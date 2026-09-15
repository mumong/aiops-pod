## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload in aiops-case-v17 was in CrashLoopBackOff state with 11 restarts; currently appears Running but in Waiting state with liveness probe failure as direct block. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-5f842d02bc01` | `Liveness probe failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers)` | 明确应用服务在 5m17s 内频繁无响应，导致 kubelet 判定存活失败 |
| 2 | K8s Event | `fact-209685741ef3` | `Container app failed liveness probe, will be restarted` | 确认存活探针失败后触发了容器重启机制 |
| 3 | K8s State | `fact-18c8b55c195a` | `last_exit_code: 137` | 进程被强制终止（OOMKilled 或 SIGKILL），印证了服务僵死后的强杀行为 |
| 4 | K8s State | `fact-31374d304ab6` | `CrashLoopBackOff` | 确认容器处于反复崩溃重启的失控循环中 |
| 5 | K8s Config | `fact-23e484595e72` | `CPU limit: 200m` | 设定了 200m 的硬限制，为服务因资源饥饿导致停滞提供环境背景 |
| 6 | K8s Config | `fact-24e41198c7e9` | `Memory limit: 64Mi` | 容器仅有 64Mi 内存限制，且进程为 `ThreadingHTTPServer`，存在极低内存上限 |
| 7 | Logging | `fact-3dc91aad7648`~`fact-372f5b5299e9` | `GET /ready HTTP/1.1 200` (21:25:38 - 21:25:55) | 日志显示就绪端点在此时间段内仍能成功响应 |
| 8 | Tracing | `fact-0cba48264420` | `GET /ready`: 200, `21:20:04` - `21:25:31` | 流量追踪印证就绪探针在崩溃前一直正常工作 |

**证据印证：**
K8s 状态（#3, #4）与事件（#1, #2）共同刻画了“服务无响应 → 探针超时 → 强杀进程”的闭环。日志（#7）和流量追踪（#8）证实服务在崩溃前（约 21:26 前）功能正常。结合事件（#1）中探针失败的时间（21:26:07）晚于日志最后记录的时间（21:25:55），确认应用是从“正常运行”突然转变为“完全无响应”。

## 🎯 根因分析 · g1

### 因果链
```text
服务因资源饥饿(如200m CPU)或代码逻辑导致死锁/僵死 → Liveness探针(5s)超时(context deadline exceeded) → 容器被kubelet强杀(Exit 137) → 进入CrashLoopBackOff状态
```

### 根因结论
**已确认根因**：应用进程（`python3 -u`）发生僵死或严重阻塞（Unresponsive），导致存活探针连续超时失败。
**依据**：
1.  kubelet 明确记录探针请求超时（`Client.Timeout exceeded`，证据 #1）；
2.  进程退出码 137 证明是被系统强制终止（证据 #3）；
3.  日志与流量在崩溃时间点（约 21:25:55）之前均为正常（证据 #7, #8）。

**未确认细节**：由于缺乏崩溃时段的堆栈或 CPU 采样数据，无法区分根本原因是 **CPU 限制（200m）导致的资源饥饿** 还是 **Python 代码内部死锁（ThreadingHTTPServer 阻塞）**。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 28.4s
├─ 并发证据采集: 117.5s
│  └─ g1 aiops-case-v17/workload: 117.5s (Evidence 106.5s, RCA 10.7s)
└─ 汇总总结: 13.8s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
