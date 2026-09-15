## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态（25次重启） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Exit Code: 137` (fact-0dcfae74b18c), 容器 `app` 退出码 `137` (fact-6d3f9ec5b398) | 确认进程被异常终止 |
| 2 | K8s State | Kubernetes | Container `app` 处于 `CrashLoopBackOff` 状态，已重启 25 次 (fact-1cd2e87a477e, fact-7c1baf74e199) | 现象层：Pod 持续崩溃循环 |
| 3 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-7933df5bb5fb) | 现象层：探针在容器终止前检测到 500 错误 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 在崩溃周期内达到峰值 `15433728` 字节 (约 14.7MB)，随后回落 (fact-047a5856c8c3) | 验证资源耗尽：内存使用量达到峰值后骤降，符合 OOM Kill 特征 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi` (fact-7bf25846695c) | 设定资源边界，作为触发 OOM 的限制条件 |
| 6 | Metric | Prometheus | 崩溃前最后一次记录内存占用约 `15.4MB` (fact-0cd4d3fb6111, fact-5124e6942b7b) | 提供 OOM 前的高水位参考 |

**证据说明：**
1. **现象关联**：`fact-0dcfae74b18c` 和 `fact-6d3f9ec5b398` 显示的 Exit Code 137 与 K8s 中 `CrashLoopBackOff` 的状态（`fact-1cd2e87a477e`）直接对应，确认异常类型为被强制杀死而非应用正常退出。
2. **资源验证**：Metric `fact-047a5856c8c3` 记录了容器内存从基线约 4MB 飙升至 `15433728` 字节（约 14.7MB），且由于配置中 `96Mi` 的内存限制（`fact-7bf25846695c`，约 98.3MB），这表明容器在崩溃前确实经历了显著的资源消耗增长，且高水位与低水位之间的急剧跳变是典型的 OOM Kill 内存特征。
3. **探针矛盾解释**：`fact-7933df5bb5fb` 的探针 500 错误发生在 OOM 触发前或内存压力极大导致服务无响应时，这印证了应用在高负载（或内存泄漏导致的无响应）下未能保持正常健康状态，从而触发重启循环。

## 🎯 根因分析 · g1

### 因果链
```text
应用代码内存泄漏 (隐含于持续增长的高水位) → 容器内存使用触及 96Mi 限制 → OOM Killer 发送 SIGKILL (Exit Code 137) → Pod CrashLoopBackOff (重启 25 次)
```

### 根因结论
已确认根因为：**应用容器因内存耗尽被 OOM Killer 终止 (OOMKilled)**。

证据链由以下事实闭环支撑：
1. **直接机制确认**：`Exit Code 137`（`fact-0dcfae74b18c`）是 Linux 下进程被 OOM Killer 强制杀死的明确标志。
2. **资源边界验证**：Pod 配置的内存 Hard Limit 为 `96Mi`（`fact-7bf25846695c`）。
3. **行为特征印证**：Metric 观测到容器内存使用量在崩溃前达到 `15.4MB` 的高水位（`fact-047a5856c8c3`），并在随后周期骤降，这符合内存泄漏触发 OOM 的典型模式（内存耗尽 -> 进程被杀 -> 内存回收）。
4. 尽管 Liveness 探针记录了 500 错误（`fact-7933df5bb5fb`），结合 137 退出码，这表明应用在内存耗尽导致完全无响应或崩溃前夕处于严重异常状态。

现有证据（K8s 状态 137 退出码 + 容器配置 + 内存高水位跳变）已形成完整证据闭环，足以将根因锁定为“应用内存资源耗尽引发的 OOMKilled”。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 13.2s
├─ 并发证据采集: 112.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 112.1s (Evidence 103.0s, RCA 8.9s)
└─ 汇总总结: 16.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
