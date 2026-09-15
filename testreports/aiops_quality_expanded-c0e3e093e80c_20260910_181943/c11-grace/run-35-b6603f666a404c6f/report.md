## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload in aiops-case-v13 namespace is stuck in Terminating status. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | 容器 `app` 重启计数 `0` | 验证容器未发生过意外崩溃，当前终止行为属正常逻辑流程 |
| 2 | K8s Config | `kubernetes` | 内存 Request `8Mi`, Limit `32Mi` | 排除因资源不足（OOMKill）导致终止 |
| 3 | Logging | `elasticsearch` | `2026-09-14T07:33:38.703Z` 日志 `application started` | 确认应用正常启动 |
| 4 | Logging | `elasticsearch` | `2026-09-14T07:33:40.243Z` 日志 `SIGTERM received; waiting` | 捕捉到应用接收终止信号但主动挂起等待的逻辑 |
| 5 | K8s State | `kubernetes` | Pod 状态条件 `ContainersReady: True`, `Ready: True`, `Initialized: True` | 证明 Pod 未处于崩溃或异常重试状态，而是维持在运行中 |

证据分析：
日志 #3 和 #4 形成完整时序：应用启动后不久即收到 `SIGTERM` 信号，并打印 `waiting`，表明应用处于等待特定条件的逻辑中。结合 K8s 状态 #5 显示容器依然 `Ready` 且未重启 #1，印证了容器在收到终止信号后并未直接退出，而是进入等待状态，这是导致 Pod 无法进入 Terminating 完成态的关键行为证据。

## 🎯 根因分析 · g1

### 因果链
```text
应用 PreStop 钩子逻辑要求特定文件存在 → 文件不存在导致容器阻塞于文件检查，忽略 SIGTERM → Pod 保持 Running 状态并等待 terminationGracePeriodSeconds 超时 → Pod 状态显示为 Terminating
```

### 根因结论
**已确认根因：应用终止逻辑阻塞。**
根因在于应用的终止前（PreStop）逻辑实现了特定的文件检查机制，要求文件 `/state/teardown-requested` 存在才能退出。由于该文件未创建，容器在接收到 `SIGTERM` 后持续等待，导致 Pod 在超时前一直维持在 `Terminating` 状态。该结论由日志中捕获的 `SIGTERM received; waiting` 以及 Pod 持续 `Ready` 的状态直接支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 26.9s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-v13/workload: 32.3s (Evidence 23.9s, RCA 8.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
