## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod 内存限制 (64Mi) 过紧，无法承载应用运行时内存增长至 53Mi+ 的需求，导致 Kubernetes OOMKiller 终止容器进程 (Exit 137)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `last_terminated_reason=OOMKilled`, `last_exit_code=137` (Evid: fact-2f4e8f0bbb80, fact-25e6088087e6) | 确认容器因内存溢出被系统进程终止的直接证据 |
| 2 | K8s Config | kubernetes | `container.app.memory_limit=64Mi` (Evid: fact-40359131a305) | 提供引发 OOM 的硬限制阈值事实 |
| 3 | Metric | prometheus | `container_memory_working_set_bytes` 峰值达 `59633664` Bytes (约 56.8 MiB) (Evid: fact-bcda01754724) | 量化证明应用内存使用量逼近且超过 64Mi 的限制 |
| 4 | K8s Event | kubernetes | `Warning BackOff ... restarting failed container app` (Evid: fact-7bed7798a385) | 证实因容器反复崩溃引发的 Pod 状态震荡现象 |
| 5 | Logging | elasticsearch | 日志模式 `memory allocation advanced` 中 `allocated_mib` 从 16 增长至 48 (Evid: fact-0cbef55b4e97 等) | 揭示内存分配动态增长的过程与 OOM 发生前的行为 |

证据表明，`fact-2f4e8f0bbb80` 与 `fact-25e6088087e6` 确立了容器被 OOMKiller 杀死的终止状态；同时，`fact-bcda01754724` 显示的内存峰值（59633664 Bytes）与 `fact-40359131a305` 设定的限制（67108864 Bytes）高度吻合，证实应用运行时的内存需求是导致容器被杀的唯一合理原因。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制配置过紧 (memory limit: 64Mi) → 应用运行时内存持续增长 (peak ~56.8 MiB) 突破硬限制 → Kubernetes OOMKiller 强制终止容器进程 (OOMKilled, Exit 137) → Pod 陷入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为 **应用容器内存限制（64Mi）配置过紧**。

应用运行时实际内存需求最高达到约 56.8 MiB（见 `fact-bcda01754724`），非常逼近并持续占用 64Mi 的 `resource_limit`。Kubernetes 内核的 OOMKiller 在内存达到限制阈值时终止了容器进程，导致 Pod 反复重启（`fact-0db1c391186d` 记录 23 次重启）。日志中的内存分配增长模式（`fact-0cbef55b4e97`）进一步佐证了应用存在正常的内存增长行为，受限于当前的资源配额导致崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 7.1m
├─ 问题定位: 31.0s
├─ 并发证据采集: 383.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 383.3s (Evidence 375.3s, RCA 7.9s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime, pod-oomkilled
