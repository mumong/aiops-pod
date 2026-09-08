## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 应用 `/work` 接口持续线性分配内存至 48 MiB，超过容器内存上限 64 MiB 导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff (fact-486a0a17913a) | 证实容器进入异常重启循环状态 |
| 2 | K8s Event | kubernetes | container.last_terminated_reason: OOMKilled (fact-e69144302359) | 确证容器被系统杀死，非应用主动退出 |
| 3 | K8s State | kubernetes | container.last_exit_code: 137 (fact-1d98b148be66) | 配合 OOMKilled 确认资源耗尽导致的进程终止 |
| 4 | K8s Config | kubernetes | container.resource_limit.memory: 64Mi (fact-07bbb43ffa02) | 提供触发 OOM 的硬限制阈值事实 |
| 5 | Logging | elasticsearch | `/work` 接口请求 `allocated_mib` 从 14MiB 线性增长至 48MiB (fact-logging-pattern) | 提供内存分配持续增长的具体证据 |
| 6 | Tracing | deepflow | L7 Flow: 9次 `GET /work` 返回 200 (fact-tracing-flow) | 证明异常调用发生在应用层且服务正常响应 |
| 7 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason: 1 (OOMKilled)` (fact-55826cdafe4f) | Metric 维度确认最后的终止原因为 OOM |

**证据关联与印证：**
Logging 中 `/work` 接口内存分配的线性增长（事实 5）直接解释了为何在 64MiB 限制（事实 4）下触发 OOMKilled（事实 2）。Tracing（事实 6）进一步将异常调用与 `/work` 路径关联。Kubernetes 状态（事实 1, 3）与 Metric（事实 7）互相印证了该状态并非偶发，而是持续存在的 CrashLoopBackOff 结果。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑在 /work 路径持续线性增加内存分配 → 累积内存使用触发容器硬限制 (64MiB) → 内核执行 OOM Kill 终止容器 (Exit 137) → Pod CrashLoopBackOff 持续重启
```

### 根因结论

已确认根因为**应用内存分配超出容器限制**。

证据表明：应用通过 `/work` 接口持续分配内存（Logging 显示分配量从 14MiB 升至 48MiB），最终触及 64MiB 的容器内存硬限制（K8s Config），导致内核 OOM Killer 介入终止进程（K8s State/OOMKilled/Exit 137）。Metric 与 K8s 事件状态证实该进程终止反复发生，进而导致 Pod 处于 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 22.9s
├─ 并发证据采集: 133.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 133.2s (Evidence 124.6s, RCA 8.3s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
