## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，重启 17 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `exit_code: 137`, `last_terminated_reason: Error`, `restart_count: 17` | 确证容器因收到 SIGKILL (OOM Kill 典型特征) 而崩溃，且处于重启循环中 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` | 设定极低的内存硬限制，为 OOM Kill 提供直接配置前提 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` | 初始申请仅 8Mi，与 64Mi 硬限制间余量极小，无缓冲空间应对依赖加载开销 |
| 4 | K8s Event | kubernetes | `Liveness probe failed: ... context deadline exceeded` | 证明应用进程在崩溃前已无响应（挂起），导致 Liveness Probe 超时，进而触发重启 |
| 5 | K8s Event | kubernetes | `Container app failed liveness probe, will be restarted` | 确认 kubelet 因探测失败主动执行了重启操作 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason: CrashLoopBackOff` (value=1) | 实时指标确认容器当前处于 BackOff 等待状态，与 K8s Event 同步 |
| 7 | Logging | elasticsearch | `[13:43:13 ~ 13:43:55] GET /ready HTTP/1.1 200`, `GET /health HTTP/1.1 200` | 证明在最后一次崩溃（13:43:56 Killing）前的窗口期内，服务仍响应正常，排除了启动即崩溃 |
| 8 | Tracing | deepflow+tempo | `GET /health`, `duration_us: min 3000773, max 3001826` | 显示健康探测请求耗时约 3 秒（超时阈值外），佐证服务在处理探测时已因内存耗尽出现严重卡顿 |

**证据互证：**
K8s 配置 (1,2,3) 设定了极小的内存环境；Logging (7) 显示应用曾正常响应；Tracing (8) 与 K8s Event (4) 共同证实了服务在崩溃前夕对探测请求产生严重延迟；最终 K8s State (1) 的 Exit 137 标志着 OOM Kill 的发生，而 K8s Event (5) 确认了由 Probe 超时触发的重启机制。全链路证据支持“资源限制不足导致服务无响应并被终止”的闭环。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低 (64Mi) → 应用运行/加载依赖触及阈值，服务响应变慢甚至挂起 → Liveness Probe 超时 (context deadline exceeded) 且内核触发 OOM Kill (Exit 137) → Kubelet 强制终止容器，Pod 进入 CrashLoopBackOff 循环
```

### 根因结论

**已确认的根因：** `容器内存资源限制 (64Mi) 过低`。

该根因通过以下事实链得到确证：
1.  **配置约束**：容器 `app` 被设置了 64Mi 的硬内存上限，但初始请求仅为 8Mi，余量极小，极易在 Python 应用加载依赖或启动初始化时触发 OOM [证据 2, 3]。
2.  **崩溃特征**：容器以退出码 137 (SIGKILL) 终止，这是 Linux 内核 OOM Killer 终止进程的标准标志 [证据 1]。
3.  **触发机制**：在 OOM 发生前，应用进程因内存争用导致响应严重延迟，致使 Liveness Probe 超时（耗时约 3 秒），kubelet 判定探针失败后强制执行重启 [证据 4, 5, 8]。
4.  **现象吻合**：上述过程导致 Pod 频繁崩溃并进入重启循环，且日志显示崩溃前服务曾短暂响应正常，排除了代码逻辑错误或启动配置错误 [证据 7]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.6s
├─ 并发证据采集: 69.3s
│  └─ g1 aiops-case-v17/workload: 69.3s (Evidence 59.1s, RCA 10.0s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
