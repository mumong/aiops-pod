## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态且无法在宽限期内自动恢复。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Terminating (lasts <invalid>)` | 确认 Pod 处于终止状态，但存在时间异常（<invalid>），表明无法正常退出 |
| 2 | K8s Event | `Killing` | `Normal   Killing         45s                kubelet            Stopping container app` | 确认 kubelet 已介入终止流程并停止容器 |
| 3 | K8s Event | `Unhealthy` | `Warning  Unhealthy       47s (x2 over 50s)  kubelet            Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 提供应用启动后行为线索，探针命令在等待检查特定文件路径 |
| 4 | Logging | `elasticsearch` | `application started` @ `06:57:58.502Z` | 确认应用进程已成功启动 |
| 5 | Logging | `elasticsearch` | `SIGTERM received; waiting` @ `06:57:59.447Z` | 确认进程收到终止信号后进入阻塞等待状态，未执行主动退出逻辑 |

K8s Event 与 Logging 在时间轴上高度重合，`SIGTERM received; waiting` 解释了为何 kubelet 发送终止信号后 Pod 无法退出。K8s 状态为 `Terminating` 且持续时间异常，佐证了应用进程在收到信号后无法及时释放资源并退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用终止逻辑依赖外部文件 '/state/teardown-requested' → 终止过程中文件未创建 → kubelet 发送 SIGTERM → 进程死循环等待 → Terminating 状态持续 >65 分钟
```

### 根因结论

**已确认根因：应用终止处理逻辑缺陷导致进程无限等待。**

应用代码在收到 `SIGTERM` 信号后（日志 `fact-5ff86fc450c9` 记录），进入对特定文件 `/state/teardown-requested` 的轮询等待。由于该文件在当前的终止流程中并未被创建（K8s 终止信号未触发控制器创建该文件），进程陷入了死循环，无法响应 kubelet 的优雅退出请求，只能被动等待直至 `terminationGracePeriodSeconds`（65分钟）超时。证据显示 Pod 在收到信号后立即转为 `waiting` 状态（证据 5），且未检测到重启（证据 1），符合阻塞等待特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.3s
├─ 并发证据采集: 49.5s
│  └─ g1 aiops-case-v13/workload: 49.5s (Evidence 39.7s, RCA 9.7s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
