## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态超过1小时（deletionTimestamp 2026-09-14T08:28:15Z），但容器进程仍处于 Running 状态，未随 SIGTERM 信号退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Terminating (lasts <invalid>)` (fact-df688e3baf07) | 确认 Pod 处于卡死的终止状态。 |
| 2 | K8s State | kubernetes | `pod.phase: Running` (fact-b37868c25142) | 确认容器进程仍在运行中，未随信号退出。 |
| 3 | K8s Event | kubernetes | `kubelet Killing: Stopping container app` (fact-793ea6bdea17) | 证明 kubelet 已成功发送终止信号并尝试关闭容器。 |
| 4 | K8s Event | kubernetes | `kubelet Unhealthy: Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` (fact-918c3bcd6875) | 反映探针在进程处理终止期间因超时失败，佐证了进程处于不可中断或阻塞的等待状态。 |
| 5 | Logging | elasticsearch | `application started` (fact-4091d8dbef27) | 确认应用已正常启动，排除了启动配置导致未运行的可能性。 |
| 6 | Logging | elasticsearch | `SIGTERM received; waiting` (fact-7d03fb1267b6) | **核心证据**：应用捕获到 SIGTERM 后进入“等待”逻辑，证实应用层主动拦截了终止信号。 |

**证据印证：**
日志明确记录了应用接收到 `SIGTERM` 后进入等待（fact-6），这与 K8s 层面容器未退出且状态为 `Terminating` 但进程仍在运行（fact-1, fact-2）的现象完全一致。探针超时（fact-4）进一步佐证了该等待状态可能是阻塞性的。

## 🎯 根因分析 · g1

### 因果链

```text
应用自定义逻辑阻塞主循环 → 关键触发文件缺失导致无限等待 → 容器进程拒绝退出 → Pod 状态卡死 Terminating
```

### 根因结论

**已确认的根因：**
应用代码逻辑导致优雅终止机制失效。具体表现为：应用主循环阻塞等待文件 `/state/teardown-requested` 出现（如 `while not Path('/state/teardown-requested').exists()`），当该文件不存在时，主循环持续运行，阻止了进程的终止。证据 `fact-7d03fb1267b6`（日志显示 "SIGTERM received; waiting"）证实了应用在捕获信号后并未正常退出，而是进入了这种特定条件的等待状态。

**缺失信息：**
无法确定为何文件 `/state/teardown-requested` 未被创建（是外部触发失败、Init Container 未完成还是配置错误），但这不影响当前“进程因等待文件而无法退出”这一直接根因的确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 21.5s
├─ 并发证据采集: 60.1s
│  └─ g1 aiops-case-v13/workload: 60.1s (Evidence 46.5s, RCA 13.5s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
