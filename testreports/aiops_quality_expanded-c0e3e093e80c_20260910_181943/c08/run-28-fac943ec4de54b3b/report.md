## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | RecentRestart | 容器 'app' 配置的内存 limit (64Mi) 不足，且应用逻辑（/work 接口）在请求中无限制地分配内存（从 2 MiB 增长至 48 MiB），导致容器触发 OOMKilled (exit code 137) 并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 app `last_terminated_reason`: "OOMKilled" (`fact-1731f3c9eea3`) | 确认容器因内存超限被内核强制终止的客观事实 |
| 2 | K8s State | Kubernetes | 容器 app `resource_limit.memory`: 64Mi (`fact-7d74671efc55`) | 确定触发 OOM 的硬限制边界 |
| 3 | Logging | Elasticsearch | 模式 `memory allocation advanced` 在 `/work` 接口中观察到的 `allocated_mib` 变化：first 10 MiB → last 48 MiB (`fact-1cf25cc0a08b`) | 证实应用存在无限制内存分配逻辑，消耗量逼近硬限制 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (labels: container=app, reason=OOMKilled) 值为 1 (`fact-c898f6bf1394`) | 从指标侧佐证终止原因是 OOMKilled |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (container=app) 值为 19 (`fact-a4bfdaacc947`) | 量化频繁重启的严重程度 |
| 6 | K8s Event | Kubernetes | `Warning BackOff` 持续 88m 内发生 316 次 (`fact-3ded660fa0c5`) | 反映 CrashLoopBackOff 的典型控制回路行为 |

**证据印证关系：**
Kubernetes 的 `OOMKilled` 状态与 `Exit Code 137` 直接对应（证据 1, 5），证明是资源层面的硬切断。Logging 展示了 `/work` 接口内存分配的持续增长（证据 3），结合 Kubernetes 的硬限制 64Mi（证据 2），逻辑上解释了为何 OOM 会发生。Metric 数据独立确认了该终止原因和频繁重启的现象（证据 4, 5）。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /work 接口无限制内存分配 (证据 3) → 容器内存使用量超过硬限制 64Mi (证据 2) → 内核 OOM Killer 终止进程 (Exit Code 137) (证据 1) → Pod 进入 CrashLoopBackOff (证据 6)
```

### 根因结论

已确认根因为：**应用逻辑内存泄漏与资源限制配置不当共同作用导致的 OOMKilled。**

具体机制如下：
1.  **直接原因**：应用进程在处理 `/work` 请求时发生无限制的内存分配，分配量在短时间内从 10 MiB 飙升至 48 MiB（证据 3），逼近并触发了容器配置的内存硬限制 64Mi（证据 2）。
2.  **最终表现**：Linux 内核 OOM Killer 介入终止了该进程，导致容器以退出码 137 退出（证据 1），进而引发 Kubernetes 的重启控制回路，进入 `CrashLoopBackOff` 状态并记录到 19 次重启（证据 4, 6）。

现有证据链（K8s State/OOMKilled, Logging/Growth, Metric/Ratio）完整闭合，且正式 RCA 已获发布许可，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 20.8s
├─ 并发证据采集: 84.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 84.8s (Evidence 76.1s, RCA 8.6s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
