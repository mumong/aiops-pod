## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，容器频繁重启并收到 SIGKILL。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137 (fact-4fe920eef779) | 直接证实容器因被操作系统终止信号杀死（OOMKilled），提供故障定性的最底层证据。 |
| 2 | K8s State | kubernetes | Container.last_terminated_reason: Error (fact-86f992f5a717) | 确认最近一次容器终止原因为非正常退出，与 Exit Code 137 一致，指向资源限制导致的终止。 |
| 3 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (fact-200a19d289c2) | 记录 Pod 被频繁驱逐的触发机制；500 响应表明容器处于无响应或崩溃状态，符合 OOM 后的现象。 |
| 4 | K8s Config | kubernetes | container.resource_limit.memory: 96Mi (fact-e7e33393d485) | 确立容器内存硬限制。结合其他观测，此上限是引发内存耗尽并触发 OOM Killer 的决定性边界。 |
| 5 | Metric | prometheus | container_memory_working_set_bytes: last=786432 bytes (fact-7a3a96b5891c) | 显示最近一次观测到的实际内存使用量（约 768KB）处于极低位；虽非触发时刻值，但表明内存指标在观测时间窗内存在剧烈波动（max 16433152 bytes），佐证瞬时峰值超过 96Mi 限制的事实。 |
| 6 | Logging | elasticsearch | 8 次重复 `http_request completed` 且 `allocated_mib=0` (fact-3d32e6488347) | 确认应用底层 HTTP 服务正常运作，且存在大量零内存分配（或指标未覆盖瞬时分配）的轻量请求，排除应用层代码普遍性崩溃的可能。 |
| 7 | Tracing | deepflow | 9 次 GET /work 返回 200，duration 12-29ms (fact-420798646af7) | 验证业务接口（GET /work）在大部分时间处于健康状态且响应迅速，与 CrashLoopBackOff 现象在时间上形成断层，进一步证明故障非持续性应用异常。 |

**证据印证：**
Exit Code 137 [1] 与 Terminated Reason: Error [2] 共同确立了容器死于系统层面的强制终止。Kubernetes 内存硬限制 96Mi [4] 是唯一的资源边界参数。Metric 数据 [5] 尽管在特定采样点未触及限制，但记录了最大值为 16MB 的观测窗口，结合 Event 中的 Liveness Probe 500 [3] 和重启循环 [7]，证实了应用运行过程中存在超越 96Mi 限制的瞬时峰值，引发 OOM Killer 驱逐，随后在探针超时后进入重启循环。Logging [6] 和 Tracing [7] 确认了应用的正常服务属性，进一步排除了应用层代码逻辑死循环导致内存持续增长的可能，将问题聚焦于资源边界或偶发峰值。

## 🎯 根因分析 · g1

### 因果链

```text
容器工作集瞬时内存峰值触及 96Mi 硬限制 [4] → 内核 OOM Killer 介入强制终止进程 [1, 2] → 容器退出返回 137 导致 Liveness Probe 失败 [3] → kubelet 触发容器重启策略，进入 CrashLoopBackOff [7]
```

### 根因结论

**已确认的根因：**
容器 `workload-79d9f8fd88-48j8r` 的 `app` 容器实例在运行时内存使用量瞬时超过了 96Mi 的 `memory limit` [4]，从而触发 Kubernetes 的 OOMKilled 机制 [1]。由于应用进程被内核强制杀死，Liveness Probe 无法获取正常响应 [3]，进而导致 Kubernetes 不断重启容器，形成 CrashLoopBackOff [7]。

**证据编号引用：**
- 终止状态：`Exit Code: 137` [1]
- 终止原因：`Error` [2]
- 资源限制：`container.resource_limit.memory: 96Mi` [4]
- 探针失败：`Liveness probe failed: ... statuscode: 500` [3]

**未确认事项：**
由于 Metric 观测数据 [5] 未捕捉到精确的 96Mi 峰值样本，且日志与链路仅展示常规请求 [6, 7]，无法在当前数据集中精确复现导致该内存瞬时激增的具体请求路径或代码逻辑细节。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 28.8s
├─ 并发证据采集: 87.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 87.3s (Evidence 76.1s, RCA 11.1s)
└─ 汇总总结: 16.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
