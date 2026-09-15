## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | 容器镜像中缺少入口命令文件 `/opt/app/unavailable-command` |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  BackOff  2m41s (x303 over 67m)  kubelet  Back-off restarting failed container app` | 确认 Pod 处于长期反复重启状态 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认当前异常组状态 |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: `127` | 确定进程退出的具体错误码 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error` | 确认容器非正常终止的原因类型 |
| 5 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接揭示命令未找到及执行方式（sh -c exec） |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=CrashLoopBackOff, value=1) | 验证 K8s State 中的等待原因 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (value=17) | 验证异常的持续性和频率 |

**证据说明**：
Kubernetes 的 `Event` 和 `State` 事实确认了 Pod 处于由 `CrashLoopBackOff` 和 `Error` 导致的重启循环中。Logging 维度中明确的 `not found` 错误原文及 `127` 退出码，在因果链上闭环，解释了为何 `CrashLoopBackOff` 机制会被反复触发。Metrics 提供了 K8s 状态的独立交叉验证，未发现冲突证据。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
容器镜像中缺失入口命令文件 `/opt/app/unavailable-command` → 容器启动时执行 `sh -c exec /opt/app/unavailable-command` 失败，shell 返回 Exit Code 127 → 容器因命令未找到异常终止（Reason=Error），kubelet 触发 CrashLoopBackOff 重启机制 → Pod 持续处于 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是**容器镜像中缺少入口命令文件 `/opt/app/unavailable-command`**。

该文件缺失导致容器启动命令执行失败（Evidence: Logging fact-3d6f1ba89f0f, K8s fact-02f34fd06295），容器以 Exit Code 127 退出，进而触发 kubelet 的 `CrashLoopBackOff` 重试机制（Evidence: K8s fact-3ba583563c90, fact-a3803b720c20）。现有证据链完整，足以支撑上述结论。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 23.8s
├─ 并发证据采集: 539.8s
│  └─ g1 aiops-case-v08/workload: 539.8s (Evidence 533.2s, RCA 6.5s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
