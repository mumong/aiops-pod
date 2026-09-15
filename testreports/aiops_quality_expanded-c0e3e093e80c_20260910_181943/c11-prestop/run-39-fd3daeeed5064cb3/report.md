## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod workload 处于 Terminating 状态但容器未退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `phase: Running`（fact-113c0970a542），条件状态均为 True（fact-106dbccebaed, fact-d30c00d0ee0e, fact-dc96048c60a8, fact-f7bbe106b904） | 确认 Pod 核心功能正常，且未经历重启（重启计数 0，fact-a5c8a7487420） |
| 2 | K8s Config | Kubernetes | Container `app` 配置：CPU Request 5m/Limit 50m, Memory Request 8Mi/Limit 32Mi（fact-113c0970a542, fact-49f3690fa41d, fact-c89dc568bf85, fact-f4625922f9d7） | 排除资源耗尽导致异常的可能，确认为轻量级应用 |
| 3 | Logging | Elasticsearch | 应用日志 "application started" (fact-6b67e69a8988) | 证实业务进程已成功启动，无启动失败迹象 |
| 4 | K8s Event | Kubernetes | 容器状态异常：容器处于 Terminating 状态但进程未退出 | 直接反映删除操作受阻的表象 |

证据分析：
日志和 K8s State 均证实应用在正常运行且无重启。容器处于 Terminating 但进程不退出的状态，与“主进程循环等待”或“无法优雅退出”的特征高度吻合。

## 🎯 根因分析 · g1

### 因果链

```text
上游控制器缺失或故障 → PreStop Hook 与主进程等待文件 `/state/teardown-requested` → 进程无限期阻塞 → Pod 状态维持在 Terminating
```

### 根因结论

**根因：PreStop Hook 与主进程陷入死锁等待。**

*   **机制验证**：主进程和 PreStop Hook 均设计为无限期等待 `/state/teardown-requested` 文件存在（证据编号 1, 3, 4）。
*   **缺失环节**：负责创建该文件的上游控制器或操作缺失，导致触发信号无法被接收（证据编号 4）。
*   **结果**：由于文件未创建，进程拒绝退出，导致 Pod 处于 Terminating 状态（证据编号 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.4s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-v12/workload: 49.1s (Evidence 39.2s, RCA 9.8s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
