## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器启动时执行 `bytearray(256*1024*1024)` 内存分配，远超 Kubernetes 设定的 64Mi 硬限制（Limit），触发内核 OOM Killer 强制终止进程（Exit 137），导致容器反复重启形成 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.resource_limit.memory` | `64Mi` | 提供内存硬限制基线，与日志分配量冲突。 |
| 2 | Logging | `log.message` | `startup allocation 256Mi` | 证实容器启动阶段请求的内存量是配置限制 4 倍的事实。 |
| 3 | K8s State | `container.last_terminated_reason` | `OOMKilled` | 确认进程被内核强制终止的直接原因。 |
| 4 | K8s State | `container.last_exit_code` | `137` | 证实收到 SIGKILL 信号（128+9）的标准终止代码。 |
| 5 | K8s State | `container.restart_count` | `13` | 证实触发 OOM 后 Kubelet 持续执行重启动作。 |
| 6 | K8s Event | `BackOff` | `Back-off restarting failed container ...` (x211 over 45m) | 确认重启频率已进入 BackOff 指数退避阶段。 |
| 7 | Metric | `kube_pod_container_status_last_terminated_reason` | `OOMKilled` | 独立观测确认 OOMKilled 为当前容器状态。 |

**证据分析：**
- 证据 1 与 2 存在显著的数量级差异：配置硬限制为 64Mi（证据 1），而启动日志明确记录分配了 256Mi（证据 2）。
- 证据 3、4、6 形成闭环，逻辑链条清晰：分配超限（证据 2）引发 OOMKilled（证据 3、7）和 SIGKILL（证据 4），进而导致 BackOff（证据 6）和持续重启（证据 5）。

## 🎯 根因分析 · g1

### 因果链

```text
启动命令分配 256Mi (日志) → 超出 64Mi cgroup 硬限制 (配置) → 内核 OOM Killer 触发 SIGKILL (Exit 137) → CrashLoopBackOff
```

### 根因结论

已确认的根因是**应用启动时的内存分配量超过了 Kubernetes 配置的 Limit**。

具体表现为：容器 `app` 在启动执行 `bytearray` 等内存分配操作时，请求了 `256Mi` 内存（见日志证据 2），而 K8s 配置的容器内存限制仅为 `64Mi`（见配置证据 1）。这一资源不匹配直接触发了 Linux 内核的 OOM Killer，以 Exit Code 137 强制终止了容器进程（见 K8s 状态证据 3、4）。Pod 随后的反复重启及 CrashLoopBackOff 状态（见事件证据 6）均为 OOMKilled 后的直接结果。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 20.4s
├─ 并发证据采集: 546.3s
│  └─ g1 aiops-case-v15/workload: 546.3s (Evidence 536.1s, RCA 10.0s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
