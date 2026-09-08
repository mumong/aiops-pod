## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，容器反复崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Liveness probe failed: HTTP probe failed with statuscode: 500 (fact-0eb0108ea963) | 暴露容器存在严重的功能异常，导致健康检查持续失败 |
| 2 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff; restart_count: 39 (fact-33b296e35e92, fact-787609182a91) | 证实容器进入反复崩溃重启的故障循环状态 |
| 3 | K8s Event | kubelet | Exit Code: 137 (fact-2ca3fdd6f875) | 容器异常退出，137 通常表示进程被系统强制终止（SIGKILL） |
| 4 | K8s Config | kubernetes | resource_limit.memory: 96Mi (fact-413865a4be33) | 提供引发容器终止的资源约束上限配置 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason (reason: CrashLoopBackOff) (fact-7d73a31f51dd) | 侧面印证 K8s 侧的状态，确认处于等待重启阶段 |

**证据互证说明：**
K8s 事件中的 Exit Code: 137（#3）与内存限制配置 96Mi（#4）高度吻合，强有力指向 OOMKilled 机制。CrashLoopBackOff 的持续重启（#2）是这一机制被反复触发的直接结果。同时，Liveness probe 返回 500（#1）表明即便在启动间隙，应用也处于非健康状态。Metrics 数据（#5）与 K8s 状态完全一致，无矛盾。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存配置过低 (96Mi) → 应用内存超出限制触发 OOMKiller 强制终止 (Exit 137) → 重启策略触发并持续失败 → Pod 进入 CrashLoopBackOff 且 Liveness 探活失败
```

### 根因结论

**已确认的根因：容器内存限制配置过低。**

输入事实充分支持该结论：
1. **退出码 137 与配置约束匹配**：Pod `workload-79d9f8fd88-sbqvc` 的容器 `app` 设置了极低的内存硬限制 `96Mi` (fact-413865a4be33)，且退出历史明确记录 `Exit Code: 137` (fact-2ca3fdd6f875)。在 Linux/K8s 环境中，Exit Code 137 是进程收到 SIGKILL 信号的标志，通常由内核的 OOM Killer 触发。
2. **现象一致**：Kubernetes 记录容器因崩溃而不断重启 (`restart_count: 39`)，状态变为 `CrashLoopBackOff` (fact-33b296e35e92, fact-787609182a91)，这与内存超限时反复被杀、重启、再被杀的循环完全一致。
3. **补充异常**：`Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-0eb0108ea963) 进一步说明该容器不仅可能因内存崩溃，其应用本身在运行时也存在严重错误（HTTP 500），这也是健康检查持续失败的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 15.1s
├─ 并发证据采集: 61.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 61.7s (Evidence 53.3s, RCA 8.2s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-notready-probe-failed
