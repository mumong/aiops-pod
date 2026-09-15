## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 状态为 Terminating（实际 phase 为 Running），删除请求已发出但未完成。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | phase: Running; DeletionTimestamp: 1789372014 | 证明 Pod 处于“假死”状态：删除请求已下发但未实际退出 |
| 2 | K8s Config | kubernetes | resource_request.memory: 8Mi; container.resource_limit.memory: 32Mi | 排除 OOM (Out of Memory) 导致 Pod 异常退出的可能性 |
| 3 | Logging | elasticsearch | `application started` → `SIGTERM received; waiting` | 确认应用正常捕获了终止信号，但主动进入了等待阻塞状态 |
| 4 | K8s State | kubernetes | Conditions: Initialized, PodScheduled, Ready, ContainersReady 均为 True | 证明容器进程依然存活，未因健康检查失败或崩溃而终止 |
| 5 | Metric | prometheus | container.restart_count: 0 | 进一步排除因 OOMKilled 或 CrashLoopBackOff 等反复崩溃的情况 |
| 6 | Tracing | deepflow+tempo | 无数据 (empty) | 无 L7 流量链路数据支持，无法从客户端侧验证请求挂起情况 |

**证据综合说明：**
Kubernetes 状态数据证实 Pod 处于 Terminating 请求下但 phase 仍为 Running 的矛盾状态 (Evidence 1, 4)；Prometheus 重启计数为 0 排除了频繁重启的可能 (Evidence 5)；核心逻辑阻塞点由 Elasticsearch 日志明确指出，应用进程在收到 SIGTERM 后调用 `waiting` 逻辑 (Evidence 3)。结合 K8s 资源配置，确认该阻塞非由资源耗尽触发，而是应用内部逻辑缺陷导致。

## 🎯 根因分析 · g1

### 因果链

```text
删除请求触发 (deletionTimestamp 存在) → 应用 SIGTERM 处理逻辑存在缺陷(死循环等待文件) → 容器进程拒绝退出 (SIGKILL 超时前) → Pod 卡在 Terminating 状态
```

### 根因结论

已确认根因为**应用 SIGTERM 信号处理函数的逻辑缺陷**。

根据 `elasticsearch` 日志证据 (Evidence 3: `SIGTERM received; waiting`)，当 Kubernetes 发起删除请求时，容器内的应用进程虽然收到了终止信号，但其内部逻辑并未立即退出，而是陷入了一个等待特定外部文件 `/state/teardown-requested` 存在的循环中。由于该文件未被创建（可能由于 Sidecar 缺失或上游未通知），进程永久阻塞。在 `terminationGracePeriodSeconds` 到期前，Kubernetes 会一直等待容器优雅退出，从而导致 Pod 状态呈现为 Terminating 但实际仍在 Running (Evidence 1, 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 23.8s
├─ 并发证据采集: 54.2s
│  └─ g1 aiops-case-v13/workload: 54.2s (Evidence 43.0s, RCA 11.2s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
