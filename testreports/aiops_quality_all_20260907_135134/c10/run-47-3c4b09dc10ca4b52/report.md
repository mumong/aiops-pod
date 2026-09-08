## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | workload-79d9f8fd88-bwqhh in CrashLoopBackOff with exit code 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态 `ContainersNotReady`; 容器 `app` 终止原因 `Error`, 退出码 `137` (fact-0f13086835a7, fact-198e898ffa00) | 证明容器被强制终止，137 通常意味着被 SIGKILL |
| 2 | K8s Event | kubernetes | `Unhealthy` 警告：`Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-d126c2afce24) | 直接触发机制：Liveness 探针失败，符合 kubelet 杀掉容器的逻辑 |
| 3 | K8s State | kubernetes | 重启次数 `42`; 事件 `BackOff` 警告 `restarting failed container` (fact-9e45ff00dbd1, fact-87bdbf1cb385) | 确认为持续循环故障，而非偶发重启 |
| 4 | Metric | prometheus | 容器重启总数 `42` (fact-d92c7aa78cdc) | 与 Kubernetes 事件记录的重启计数一致 |
| 5 | Logging | elasticsearch | 应用正常服务日志：`/work` 路径返回 HTTP 200 (fact-6aaf60f76f5b, 聚合 8 次) | 证明应用逻辑本身正常运行，故障仅限于探针探测 |

证据 1、2 共同解释了容器的终止行为：探针返回 500 导致 kubelet 发送 SIGKILL（退出码 137）并重启。证据 3 和 4 确认了该过程已循环 42 次。证据 5 指出应用其他端点正常，限定了故障范围在探针逻辑或探测端。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness 探针返回 HTTP 500 → kubelet 判定不健康并 Kill 容器 (SIGKILL) → 容器退出码 137 且重启 → CrashLoopBackOff
```

### 根因结论

**根因确认：** 容器 `app` 的 Liveness 探针配置不当或探针专属路径逻辑错误。

**分析：**
1.  **触发因素**：Kubernetes 事件明确记录探针探测失败并返回 HTTP 500 (证据 #2)，这是容器被杀的直接原因。
2.  **终止机制**：容器以退出码 137 终止 (证据 #1)，这与 kubelet 在探针失败后执行 `SIGKILL` 的行为一致。
3.  **循环表现**：由于应用并未完全崩溃，重启后可能再次因相同原因被杀，导致 42 次重启循环 (证据 #3, #4)。
4.  **应用状态**：应用其他端点 `/work` 正常响应 200 (证据 #5)，说明应用进程未发生 OOM (137 排除 OOM 的 137 伴随内存事件，且日志中 memory 为 0) 或逻辑崩溃，故障点局限于探针探测行为。

---

## 📊 性能统计

```text
├─ 总耗时: 4.2m
├─ 问题定位: 17.2s
├─ 并发证据采集: 224.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 224.0s (Evidence 210.7s, RCA 13.1s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- 未调用 Runbook
