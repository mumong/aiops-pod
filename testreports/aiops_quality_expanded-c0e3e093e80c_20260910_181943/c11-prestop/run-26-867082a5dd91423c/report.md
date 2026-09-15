## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'ContainersReady', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v12/workload` | Phase: Running; Conditions: `ContainersReady=True`, `Ready=True` (05:35:40-43Z) | 确认容器进程存活且状态健康，但 Pod 整体处于 Terminating 状态 |
| 2 | K8s Config | Container `app` | Memory Limit: `32Mi`; Request: `8Mi` | 提供资源上下文，排除了因 Memory Limit 触发 OOMKilled 导致重启的可能 |
| 3 | Logging | Elasticsearch | Log: `application started` (05:35:49Z) | 确认应用启动成功，但无 PreStop 钩子执行日志（如 `prestop-started`） |

当前证据呈现状态冲突：Kubernetes 显示容器状态正常（`Running`, `Ready=True`），但缺乏应用层退出日志或 PreStop 执行痕迹，无法判断是应用逻辑异常还是外部控制流异常。

## 🎯 根因分析 · g1

### 因果链

```text
未知触发源 → 容器未响应终止信号或钩子未执行 → 优雅关闭失败 → Pod 处于 Terminating 但容器未退出
```

### 根因结论

**证据不足。**

现有事实仅证实容器在 Terminating 状态下保持存活（`phase: Running`），但无法确定导致该状态的具体机制。已知应用已启动（#3），且无 OOMKilled 或资源限制导致的异常（#2）。决定性证据缺失，需确认以下事实：
1. **PreStop 钩子执行状态**：是否有日志证明 PreStop 开始执行，或是否因配置问题未触发。
2. **Teardown 信号链**：是否存在 `/state/teardown-requested` 文件，以及应用进程是否因卡死或信号屏蔽未能响应 Killing 信号。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.6s
├─ 并发证据采集: 48.8s
│  └─ g1 aiops-case-v12/workload: 48.8s (Evidence 36.7s, RCA 12.1s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
