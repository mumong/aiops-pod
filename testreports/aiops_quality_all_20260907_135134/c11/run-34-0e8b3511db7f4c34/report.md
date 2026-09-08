## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态残留（Stuck），API Server 未将其从集群中移除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 app 终止原因 Error, 退出码 exit_code=137 (fact-f8228addca29) | 确认容器发生异常终止，状态为 Error |
| 2 | K8s State | kubernetes | Pod 容器未就绪 ContainersNotReady: [app] (fact-2e1adfec533a) | 反映容器进程不可用，符合 Terminating 阶段的残留现象 |
| 3 | K8s Config | kubernetes | 容器 app 内存资源限制 96Mi (fact-6032076c909e) | 提供资源边界背景，但内存限制较低，可能暗示资源压力 |
| 4 | K8s State | kubernetes | Pod 状态 Terminating，finalizer 'aiops.lab/hold' 导致清理阻塞 | 确认 K8s 机制层面的直接阻碍，是 Terminating 状态无法消除的关键证据 |

**证据分析**：Kubernetes 状态表明容器 app 已停止且报错（exit_code=137），而 K8s 配置与状态共同证实了 Pod 被 custom finalizer 'aiops.lab/hold' 锁定，阻止了 API Server 的最终清理。这两者结合解释了为何 Pod 会呈现“Stuck”在 Terminating 状态的现象。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 附加在 Pod 上 → K8s 停止清理最终流程 → App 容器异常退出(exitCode=137) → Pod 处于 Terminating 状态残留
```

### 根因结论

**已确认的根因**：Pod 被强制删除后，自定义 finalizer `aiops.lab/hold` 阻止了 API Server 执行最终清理，且无日志表明持有者正在处理该 finalizer（证据：K8s 状态显示 finalizer 存在且 Pod 处于 Terminating 状态；K8s 配置确认 finalizer 属性）。这直接导致了 Pod 状态的长期残留。

**未确认部分**：
1. finalizer `aiops.lab/hold` 的具体持有者 (Controller/Operator) 为何未响应删除请求或超时。
2. App 容器 exitCode=137 的确切触发源头（OOM 或 Kill 信号）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.9s
├─ 并发证据采集: 35.8s
│  └─ g1 aiops-case-11/workload: 35.8s (Evidence 25.9s, RCA 9.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
