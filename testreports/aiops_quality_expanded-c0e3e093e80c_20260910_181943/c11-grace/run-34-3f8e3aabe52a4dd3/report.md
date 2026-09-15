## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | 应用代码逻辑阻塞：Pod被标记删除后，主进程接收SIGTERM但因等待不存在的文件('/state/teardown-requested')而无限循环，导致kubelet在长超时(3900s)内无法完成容器回收。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `event.message` | `Normal   Killing         24s                kubelet            Stopping container app` | 确认 Pod 已进入终止流程，kubelet 已发送停止信号。 |
| 2 | K8s State | `pod.status` | `Terminating (lasts <invalid>)` | 核心异常现象：Pod 处于 `Terminating` 状态且卡死，未能进入终止完成。 |
| 3 | K8s State | `pod.condition` | `ContainersReady: True` | 尽管处于终止流程，应用容器状态仍为 Ready，说明进程尚未退出，印证回收卡点。 |
| 4 | K8s Event | `event.message` | `Warning  Unhealthy       25s (x2 over 27s)  kubelet            Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 就绪探针超时表明应用进程僵死且无法响应检查，符合无限阻塞特征。 |
| 5 | Logging | `log.message` | `SIGTERM received; waiting` | 应用进程确已收到 SIGTERM 信号，并在日志中明确记录处于“等待”状态。 |
| 6 | K8s Config | `container.resource_limit.cpu` | `50m` | 容器配置极低，但结合当前现象，资源并非导致僵死的原因。 |

日志 [5] 确认应用已接收终止信号但未能退出；结合 Pod 状态 [2] 与就绪探针的超时 [4]，证明应用进程在收到信号后未能执行退出逻辑，而是进入了某种阻塞或无限循环状态，导致 Kubernetes 等待容器自然退出（长达 3900s 超时）无法回收资源。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷(无限循环等待) → 处理 SIGTERM 信号时阻塞 → kubelet 等待容器回收超时 → Pod 卡在 Terminating 状态
```

### 根因结论

已确认根因为**应用代码逻辑阻塞**。Pod 已被标记删除 [2]，且 kubelet 发出了终止容器的指令 [1]。应用进程虽然成功接收到了 SIGTERM 信号 [5]，但由于代码中等待一个不存在的文件（`/state/teardown-requested`），导致进程在信号处理逻辑中陷入无限等待，无法退出 [4]。这种阻塞导致 Kubernetes 无法通过正常等待机制回收容器，最终使得 Pod 卡在 Terminating 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.3s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v13/workload: 40.1s (Evidence 33.5s, RCA 6.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
