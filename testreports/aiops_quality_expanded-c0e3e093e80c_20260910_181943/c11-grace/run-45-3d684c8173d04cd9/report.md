## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，容器未退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器状态 `Running`, 重启次数 0 | 证实容器仍在运行中，未发生崩溃重启 |
| 2 | K8s State | kubernetes | 资源限制 `CPU: 50m`, `Memory: 32Mi` | 排除资源限制导致 OOMKilled 或资源争用的可能 |
| 3 | K8s Config | kubernetes | `resource_request.cpu: 5m`, `resource_request.memory: 8Mi` | 辅助背景：非资源超配场景 |
| 4 | Logging | elasticsearch | `2026-09-14T07:59:54.803Z application started` | 确认应用已正常启动 |
| 5 | Logging | elasticsearch | `2026-09-14T07:59:56.495Z SIGTERM received; waiting` | 核心症状：捕获终止信号并进入等待态，直接证实阻塞逻辑 |
| 6 | Metric | prometheus | `kube_pod_status_phase` Running=1 | 独立确认 Pod 运行状态，无 `Succeeded` 或 `Failed` 状态 |

**证据印证说明：**
Kubernetes 的 `running` 状态与 `restart_count=0` 表明容器没有因错误重启。结合 Elasticsearch 日志中明确的 `SIGTERM received` 后紧跟的 `waiting`，证实容器并未按照常规优雅退出流程（如直接返回或关闭连接）结束，而是主动阻塞。Metric 数据与 K8s 状态一致，确认了容器长期处于非终态运行中，排除了瞬时故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod deletionTimestamp 已设置 → kubelet 发送 SIGTERM 信号 → 应用捕获 SIGTERM 后陷入 while not Path('/state/teardown-requested').exists() 循环 → 容器无法退出，Pod 保持 Terminating 状态
```

### 根因结论

**已确认根因：应用代码中包含阻塞式优雅终止逻辑（#5 日志）**

应用进程在捕获 SIGTERM 信号后，没有直接进行资源清理并退出，而是执行了轮询等待逻辑，检查特定文件（`/state/teardown-requested`）是否存在。由于该文件未被外部触发创建，容器永久卡在等待循环中，导致 Kubelet 无法终止该容器，进而使整个 Pod 僵死在 `Terminating` 状态（#1, #2 状态及 #6 指标证实）。

**未知项：**
1. `/state/teardown-requested` 文件是否会在未来某个时刻被外部触发创建（若不会，则为永久僵死）。
2. Pod 的 `deletionTimestamp` 距今是否已超过 `terminationGracePeriodSeconds`（设定为 3900s），若已超过且仍未强制杀死，可能涉及 kubelet 或节点层面的异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.0s
├─ 并发证据采集: 46.0s
│  └─ g1 aiops-case-v13/workload: 46.0s (Evidence 37.2s, RCA 8.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
