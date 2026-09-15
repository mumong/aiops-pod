## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Application custom SIGTERM handler blocks exit until external trigger file exists |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes Pod | 状态 `Terminating` | 确定实体当前所处的核心异常状态 |
| 2 | K8s State | Kubernetes Pod | 运行时长 `<invalid>` | 证实 Pod 已启动但长时间无法脱离该状态 |
| 3 | K8s Event | Kubernetes Kubelet | `Normal Killing 43s kubelet Stopping container app` | 证明 K8s 正常下发终止信号 |
| 4 | Logging | Elasticsearch | `2026-09-14T06:38:29.790Z SIGTERM received; waiting` | 确认进程收到信号但未退出，而是主动进入等待逻辑 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 佐证无频繁重启，属于单次正常的生命周期卡死 |

证据内容说明：
1. 证据 3 与 4 互为印证，证明容器进程接收到了 K8s 的 `SIGTERM` 信号，但并未立即退出。
2. 证据 1 与 4 结合，解释了为何 K8s 认为 Pod 应被终止，但实际状态一直停滞在 `Terminating` 且无重启行为。

## 🎯 根因分析 · g1

### 因果链

```text
K8s 触发 Pod 终止 → 发出 SIGTERM 信号 → 应用程序自定义处理逻辑阻塞等待 → Pod 处于 Terminating 状态
```

### 根因结论

已确认的根因为：应用程序自定义的 `SIGTERM` 信号处理程序存在阻塞，导致容器在收到信号后不会立即退出，而是必须等待外部触发文件存在才能继续执行退出逻辑。

这一行为直接导致了 Pod 在 K8s 层面被标记为 `Terminating` 并无限期滞留。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.7s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-v13/workload: 36.7s (Evidence 32.3s, RCA 4.3s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
