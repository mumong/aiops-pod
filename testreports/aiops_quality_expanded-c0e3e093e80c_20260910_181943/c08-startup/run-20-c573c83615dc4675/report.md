## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload in aiops-case-v15 is in CrashLoopBackOff with OOMKilled (Exit 137) upon startup. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `BackOff restarting failed container app ...` (258次 over 55m) | 证明应用启动后立即失败，触发 K8s 指数级退避重启 |
| 2 | K8s State | K8s | `reason: OOMKilled`, `exit_code: 137`, `restart_count: 15` | 证实容器因内存超限被宿主机 OOM Killer 强制终止 |
| 3 | K8s Config | K8s | `container.resource_limit.memory: 64Mi`, `resource_request.memory: 8Mi` | 提供导致 OOM 的约束环境：内存硬限制仅为 64MB |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1 (OOMKilled)`, `restarts: 15` | 从监控侧印证容器多次被 OOM 终止且正在重启循环中 |
| 5 | Logging | Elasticsearch | `startup allocation 256Mi` (2026-09-14T09:52:58.605Z) | 揭示应用启动时尝试分配 256Mi，远超容器限制 |

**证据互证说明：**
应用日志显示启动时需 256Mi 内存（#5），而 K8s 配置仅授予 64Mi 限制（#3）。这一资源冲突导致容器启动瞬间触发宿主机的 OOM Killer，以 Exit 137 代码终止（#2, #4）。K8s 随后进入 CrashLoopBackOff 循环，重启次数已达 15 次，最近 24 秒内仍有 BackOff 事件（#1）。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(64Mi) < 启动分配(256Mi) → 触发宿主内核 OOM Killer → 容器以 Exit 137 被杀 → Pod 进入 CrashLoopBackOff 循环
```

### 根因结论

**已确认根因**：Pod `aiops-case-v15/workload` 的容器内存硬限制配置（64Mi）严重低于应用程序启动时的内存分配需求（256Mi）。

该配置错误导致容器在启动阶段立即触发 OOM Killer，以 137 状态码退出。Kubernetes 随后尝试重启容器，但受限于 CrashLoopBackOff 机制，应用陷入“启动-内存不足-被杀-退避”的无限循环中，导致 Pod 持续处于 `CrashLoopBackOff` 状态且不可用 [证据 #2, #3, #4, #5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 28.0s
├─ 并发证据采集: 55.1s
│  └─ g1 aiops-case-v15/workload: 55.1s (Evidence 44.2s, RCA 10.7s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
