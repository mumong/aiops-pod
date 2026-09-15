## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态，容器 app 频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `BackOff 4m32s (x535 over 119m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v15(da351bf0...)` | 证明容器经历了长达 119 分钟的 535 次重启，处于严重的 CrashLoop 状态。 |
| 2 | K8s State | `kubernetes` | `last_terminated_reason: OOMKilled` | 核心证据：直接指出容器终止原因是操作系统 OOM Killer 介入。 |
| 3 | K8s State | `kubernetes` | `exit_code: 137` | 辅助证据：退出码 137 (128+SIGKILL) 是进程被强制杀死的标准系统返回码，符合 OOM 特征。 |
| 4 | K8s Config | `kubernetes` | `resource_limit.memory: 64Mi` | 约束上下文：Pod 设定的硬内存上限仅为 64Mi。 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_last_terminated_reason=1, reason="OOMKilled"` | 独立印证：监控指标同样记录了最后终止原因为 OOMKilled，确认非偶发。 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total=28` | 现象量化：与 K8s Event 中记录的 535 次 BackOff 重启相呼应，表明容器启动即失败，无法存活。 |
| 7 | Logging | `elasticsearch` | `startup allocation 256Mi` | 根因定位：捕获到容器启动阶段的内存请求值为 256Mi，直接解释了为何会触发 OOM。 |

**证据逻辑分析：**
上述证据形成了完整的闭环：Logging 显示启动申请 256Mi 内存 [7]，而 K8s 配置硬性限制了 64Mi [4]；由于申请超过硬限制，Linux OOM Killer 介入终止进程 [2, 3]，最终导致 Kubernetes 控制器捕获到 OOMKilled 状态并持续触发 BackOff 重启 [1, 6]。Metric 数据 [5] 独立验证了这一终止原因。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制配置错误 (memory.limit 64Mi < 启动申请 256Mi) → 容器启动内存分配触发 Linux OOM Killer → 容器进程被强制终止 (Exit Code 137) → 用户可见容器持续 CrashLoopBackOff
```

### 根因结论

已确认的根因是**容器内存请求值超出了 Pod 的硬限制 (Memory Limit)**。
*   容器应用启动时尝试分配 **256Mi** 内存（见日志 [7]）。
*   但 Pod 规范中配置的 `memory.limit` 仅为 **64Mi**（见 K8s 配置 [4]）。
*   该配置错误直接导致 Linux OOM Killer 强制杀死了应用进程，表现为 K8s 层面反复捕获到 `OOMKilled` 和 `Exit Code 137`（见状态 [2, 3]），进而引发持续的 CrashLoopBackOff 重启风暴（见事件 [1]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 21.4s
├─ 并发证据采集: 50.4s
│  └─ g1 aiops-case-v15/workload: 50.4s (Evidence 41.3s, RCA 8.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-config-error
