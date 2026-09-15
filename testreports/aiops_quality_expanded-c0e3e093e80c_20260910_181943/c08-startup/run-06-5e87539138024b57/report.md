## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload in aiops-case-v15 is in CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | 容器 app 终止原因 `OOMKilled`，退出码 `137` (fact-8a18a09819ef, fact-662fdbd7d9d7) | 确认进程是被内核强制终止，直接指向资源耗尽 |
| 2 | K8s Config | K8s Config | 容器 memory limit 设置为 `64Mi`，request 为 `8Mi` (fact-93573a5664bc, fact-242ee3326638) | 定义内存硬限制，确认可用的最大内存边界 |
| 3 | Logging | Logging | 应用启动日志显示 `startup allocation 256Mi` (fact-0e0f3b5f125d) | 确认应用启动阶段即请求 256Mi 内存，远超 64Mi 的 limit |
| 4 | K8s Event | K8s Event | 警告信息：`BackOff restarting failed container app`，状态为 `CrashLoopBackOff` (fact-9c4651ac205a, fact-5e9c15938245) | 描述当前 Pod 处于反复重启的故障现象 |
| 5 | Metric | Metric | `kube_pod_container_resource_limits` 确认 memory limit 值为 `67108864` bytes (fact-35b403f64ad7) | 从 Prometheus 维度交叉验证内存 limit 配置确实为 64Mi |

**证据印证说明：**
Kubernetes 的 `OOMKilled` 和退出码 137 与 Prometheus 中的内存 limit 指标一致（证据 #1, #5）。核心矛盾在于应用启动分配内存（256Mi，证据 #3）与容器内存硬限制（64Mi，证据 #2）之间存在严重不匹配（256Mi > 64Mi），这构成了触发 OOM Killer 的决定性证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动逻辑分配 256MiB 内存 → 容器 memory limit 仅配置 64MiB → 请求内存超过硬限制触发内核 OOM Killer → 进程以 137 退出并进入 CrashLoopBackOff
```

### 根因结论

**已确认根因**：应用配置的内存资源请求与容器内存限制严重不匹配。
应用启动时尝试分配 256Mi 内存（证据 #3），但 K8s 容器规格中的 memory limit 仅为 64Mi（证据 #2, #5）。由于请求量远超内核允许的上限，直接触发 OOM Killer 导致进程被杀（证据 #1），进而引发 Kubelet 的反复重启机制（证据 #4）。该因果链被 Kubernetes 状态、日志内容和指标数据交叉印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.3s
├─ 并发证据采集: 67.8s
│  └─ g1 aiops-case-v15/workload: 67.8s (Evidence 57.7s, RCA 10.0s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-oomkilled, pod-crashloop-runtime
