## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，Liveness 探针失败导致容器被 Kill。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container exit_code: 137 (OOMKill) | 核心证据：Exit Code 137 直接证实进程被系统 OOM Killer 终止 |
| 2 | K8s Config | kubernetes | container memory_limit: 96Mi | 约束条件：极低的内存硬限制，极易被业务突发占用触发 OOM |
| 3 | K8s Event | kubernetes | kubelet: "Liveness probe failed: HTTP probe failed with statuscode: 500" | 异常现象：Liveness 探针返回 500 错误，导致 kubelet 主动 Kill 容器 |
| 4 | K8s Event | kubernetes | kubelet: "Container app failed liveness probe, will be restarted" | 直接原因：kubelet 判定探针失败，触发容器重启 |
| 5 | K8s State | kubernetes | container restart_count: 6, reason: CrashLoopBackOff | 状态现象：6 次重启后进入 CrashLoopBackOff，符合 OOM 后重启 -> 探针失败 -> 再重启的循环 |
| 6 | Metric | prometheus | container restart_count: 6, reason: CrashLoopBackOff | 交叉印证：PromQL 确认了 6 次重启和当前的 CrashLoopBackOff 状态 |

**证据关联说明：**
- 证据 #1 (Exit 137) 与证据 #2 (内存限制 96Mi) 构成了 OOM 的闭环：极低的内存限制导致了进程被 OOM Kill。
- 证据 #3 和 #4 解释了为什么 OOM 重启后会再次被 Kill：容器重启后，应用对 Liveness 探针返回 500，导致 kubelet 再次判定失败。
- 证据 #5 和 #6 确认了上述双重因素（OOM 和 探针 500）共同作用的结果：Pod 陷入了重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(96Mi)不足且可能存在内存突发 → 触发 OOMKill (Exit Code 137) → 容器被系统终止 → 容器重启
容器重启后 → Liveness 探针返回 HTTP 500 → kubelet 判定探针失败 → 容器被再次 Kill → CrashLoopBackOff
```

### 根因结论

已确认根因：**容器内存资源限制（96Mi）不足导致 OOMKilled，且应用对 Liveness 探针端点返回 500 错误，双重因素触发重启循环。**

- **内存限制不足**：容器被分配的内存限制仅为 96Mi（证据 #2），这在面对业务负载时极易被占满。当内存超限，操作系统内核的 OOM Killer 介入，导致容器进程以 Exit Code 137 终止（证据 #1）。
- **探针失败**：容器每次被 OOM 重启后，应用未能及时恢复健康状态，Liveness 探针在探测时持续返回 HTTP 500 错误（证据 #3, #4）。这导致 kubelet 认为容器虽然正在运行（或刚启动），但应用层已不健康，因此主动 Kill 容器。
- **循环机制**：OOM Kill 和探针失败的双重作用，使得 Pod 无法进入稳定的 Running 状态，最终表现为 CrashLoopBackOff（证据 #5, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 17.6s
├─ 并发证据采集: 100.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 100.1s (Evidence 90.0s, RCA 9.9s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
