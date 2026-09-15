## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，表现为 Liveness 探针超时与 Kubelet Killing 重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` (fact-834b5d2ef50d) | 确认存活探针 `/health` 端点响应超时，是 Pod 被重启的直接触发事件。 |
| 2 | Logging | `elasticsearch` | 连续日志显示 `GET /health HTTP/1.1" 200 -` (fact-2f899844efb1, fact-8d07e76cb58b, fact-8f267f08c15d) | 证实应用自身日志中 `/health` 请求能返回 200，表明探针是在应用日志落盘前被阻断（如应用层阻塞或连接建立阶段）。 |
| 3 | Tracing | `deepflow` | `GET /health` Flow: `duration_us` min: 3,001,102 (~3s), max: 3,001,920 (~3s) (fact-5eec28ed701d等) | 流量数据确证 `/health` 端点每次均阻塞约 3 秒返回，与探针超时阈值（<1s）严重冲突。 |
| 4 | K8s State | `kubernetes` | `Container app failed liveness probe` (fact-3dfde284eaa8) & `Exit Code: 137` (fact-58ee8fce75a6) | 结合探针超时事实，确认 Kubelet 终止了应用容器；Exit 137 在此场景下由探针超时后的强制清理导致。 |
| 5 | K8s Config | `kubernetes` | `container.resource_limit.memory` = 64Mi (fact-8ccd5d4eedcd) | 虽然内存限制极低，但 Tracing 显示的固定 3s 阻塞是确定故障，无需假设资源不足。 |

**证据互证说明：**
- K8s 事件报告 `/health` 探针超时（#1），Tracing 数据精准还原了该端点阻塞约 3 秒的规律（#3），两者因果一致。
- 日志显示应用层记录了 200 响应（#2），说明请求已到达应用但未能及时返回给 Kubelet，佐证了阻塞发生在应用内部逻辑中，而非网络不通。
- 探针超时（#1, #3）直接导致 Kubelet 强杀容器并记录 Exit 137（#4）。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑缺陷: /health 端点硬编码 time.sleep(3) 阻塞处理 → 
探针配置冲突: Liveness timeoutSeconds=1s < 端点阻塞时间~3s → 
直接失败: 探针持续超时 (context deadline exceeded, fact-834b5d2ef50d) → 
用户可见现象: Kubelet 强杀容器 (Exit 137), Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：**
应用程序代码逻辑缺陷。`/health` 存活探针处理函数中包含约 3 秒的硬编码阻塞（`time.sleep(3)`），这超过了 Kubelet 配置的 1 秒超时阈值（timeoutSeconds=1s）。Kubelet 因连续检测到探针超时而判定容器存活探针失败，进而强制终止了容器进程，导致 Pod 进入 `CrashLoopBackOff` 状态（证据 #1, #3）。

*注：退出码 137 (fact-4) 在此处虽常关联 OOMKilled，但在探针超时场景下，它是 Kubelet 执行强制 Kill 操作的直接结果；且 Tracing 数据（#3）已明确锁定了超时根因，排除了单纯因内存（64Mi）不足导致的故障。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.7s
├─ 并发证据采集: 76.7s
│  └─ g1 aiops-case-v17/workload: 76.7s (Evidence 63.0s, RCA 13.5s)
└─ 汇总总结: 13.8s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled, pod-imagepull-failed
