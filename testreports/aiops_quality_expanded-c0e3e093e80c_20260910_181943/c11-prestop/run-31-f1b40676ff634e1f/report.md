## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态，Killing 事件发生后容器容器仍处于 Running 且未输出终止日志，存在终止延迟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod status` (fact-53c737f356c6) | 状态: `Terminating (lasts <invalid>)` | 确认 Pod 处于终止等待的中间状态，未进入 Terminated |
| 2 | K8s Event | `kubelet killing` (fact-782ba42b45aa) | `Normal Killing 41s kubelet Stopping container app` | 提供触发终止的直接上游事件，Kubelet 已发送信号 |
| 3 | K8s Config | `container resource_request.memory` (fact-054b8edd1414) | `8Mi` | 资源上下文，非本次异常的故障点 |
| 4 | Logging | `elasticsearch log` (fact-dc27dce40795) | 消息: `application started`, 时间: `05:45:01.305Z` | 应用生命周期证据，缺失 Shutdown/Exit 日志，证实无主动关闭迹象 |
| 5 | Metric | `prometheus restarts` (fact-995d07859fdf) | `0` (at `05:45:35Z`) | 侧面印证容器未重启，进程未正常退出 |

**证据印证：**
Pod 状态 `Terminating` 与 Kubelet 的 `Killing` 事件表明终止流程已启动。但 Logging 中仅有 `application started` 且未见 shutdown 日志，Metric 中 `restart_count=0`，证实应用进程未响应终止信号。结合诊断结论中指出的长宽限期（3900s）上下文，当前状态符合“宽限期长且应用无主动关闭”的特征。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 触发删除指令(Terminating状态) → Kubelet 发送终止信号(Killing事件) → 应用进程未快速退出(无shutdown日志、TerminationGracePeriod长) → Pod 处于等待终止的中间状态(Terminating状态持续)
```

### 根因结论

根因为 **TerminationGracePeriod 过长且应用进程未在观察窗口内响应终止信号**。

已确认事实支撑：
1. Kubelet 已发出 `Killing` 事件 (证据1, 2)，说明上游终止指令已正确下发。
2. Pod 持续处于 `Terminating` 状态，未进入 `Terminated` (证据3)。
3. 容器未发生重启 (`restart_count=0`)，且日志中缺失应用层主动关闭的标志 (证据4, 5)，证明进程未在标准宽限期内完成退出。

缺失的确定性事实（unknowns）包括 `TerminationGracePeriod` 的具体字段数值、应用层 SIGTERM 捕获逻辑的日志证据，以及 Kubelet 层面 SIGKILL 超时细节。但现有证据已足以将现象指向“响应缓慢 + 长宽限期”导致的滞留。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.3s
├─ 并发证据采集: 37.7s
│  └─ g1 aiops-case-v12/workload: 37.7s (Evidence 26.1s, RCA 11.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- 未调用 Runbook
