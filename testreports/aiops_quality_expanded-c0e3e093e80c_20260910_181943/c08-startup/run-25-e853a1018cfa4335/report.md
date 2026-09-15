## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 中的 app 容器被配置为一次性分配 256Mi 内存（`bytearray(256*1024*1024)`），而 k8s YAML 中设置的上限仅为 64Mi，导致容器触发 OOMKilled 并被 cgroup 强制终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: `OOMKilled`; `exit_code`: `137` | 确认容器因内存超限被 cgroup 强制终止 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `restart_count`: `17` | 确认容器反复重启且处于不可用状态 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: `64Mi`; `container.resource_request.memory`: `8Mi` | 提供容器内存硬性上限，与代码需求形成矛盾 |
| 4 | Logging | Elasticsearch | `startup allocation 256Mi` | 直接证实代码层启动时尝试申请 256Mi，远超配置限制 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `2` → `17` (window 63 samples) | 确认故障复现具有持续性，且重启行为符合 OOM 特征 |

**证据说明：**
1.  **因果闭环**：日志中的 `startup allocation 256Mi` (#4) 是触发点，它直接违反了 K8s 配置的硬性上限 `64Mi` (#3)。
2.  **机制验证**：违反配置后，Linux 内核 OOM Killer 介入，导致 `exit_code 137` (#1) 和 `OOMKilled` 状态 (#1)。
3.  **结果确认**：Kubernetes 执行重启策略，导致容器陷入 `CrashLoopBackOff` 并不断累积重启次数 (#2, #5)。Metric 的上升轨迹印证了该故障在采集窗口内的持续性。

## 🎯 根因分析 · g1

### 因果链
```text
容器内存配置限制 (64Mi) 与代码逻辑需求 (256Mi) 不匹配 → 应用启动时尝试分配超出限制的内存 → 触发 Linux cgroup OOM Killer，容器被 SIGKILL 退出 (code 137) → Kubernetes 执行重启策略，Pod 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：容器资源限制配置与实际运行代码的内存需求不匹配。**

应用代码在启动时试图一次性分配 256Mi 内存（由日志 `startup allocation 256Mi` #4 证实），而 Pod 的 YAML 配置仅为其分配了 64Mi 的内存上限（#3）。这一配置与需求的严重冲突直接触发了 Linux 内核的 OOM Killer，导致容器进程被杀死（#1）。随后，Kubernetes 的重启策略使 Pod 陷入 CrashLoopBackOff 状态（#2, #5）。

证据链完整，无需补充事实即可定论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.0s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-v15/workload: 46.7s (Evidence 38.0s, RCA 8.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
