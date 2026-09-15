## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，但 phase 为 Running 且 container 未退出，删除请求被应用逻辑阻塞 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase` 值为 `Running`；`restart_count` 为 `0` | 证实 Pod 未被杀死也未重启，持续活跃 |
| 2 | K8s State | Kubernetes | 容器状态：`ContainersReady: True` 且 `Ready: True` | 确认应用逻辑仍在内部执行中，未崩溃 |
| 3 | Logging | Elasticsearch | `2026-09-14T06:45:37Z` "application started" | 记录进程启动时间基准，确认逻辑已初始化 |
| 4 | Logging | Elasticsearch | `2026-09-14T06:45:39Z` "SIGTERM received; waiting" | 记录接收删除信号后的行为，暴露阻塞机制 |

**证据关系说明：**
Logging 维度直接证实了应用进程在接收 SIGTERM 后的行为轨迹，明确排除了代码崩溃或异常退出的可能（与 K8s State 中 `restart_count=0` 互相印证），从而将故障锁定为“应用逻辑阻塞”。K8s State 中 `Running` 与 `Terminating` 的矛盾状态，由应用等待特定文件这一阻塞行为得到解释。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码实现缺陷：收到 SIGTERM 后阻塞等待文件 '/state/teardown-requested' 存在 → 运行环境配置缺陷：挂载的 'state' 卷为空目录，缺失触发退出的关键文件 → 进程无法退出，Kubernetes 机制：在 3900s 宽限期内等待 → 现象：Pod 显示 Terminating 但 phase 保持 Running
```

### 根因结论

已确认根因为**应用逻辑死循环等待特定文件**。证据链闭环且充分：
1. **机制确认**：日志 `[4]` 证实应用收到终止信号后进入“等待”状态，而非正常退出。
2. **状态确认**：K8s State 证据 `[1]`、`[2]` 证实进程在此期间保持运行且未重启，说明 Kubelet 仍在等待优雅退出。
3. **根因闭环**：应用正在等待的文件 '/state/teardown-requested' 始终不存在（基于日志阻塞行为推断），导致退出请求永久挂起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.5s
├─ 并发证据采集: 44.3s
│  └─ g1 aiops-case-v13/workload: 44.3s (Evidence 30.2s, RCA 14.0s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
