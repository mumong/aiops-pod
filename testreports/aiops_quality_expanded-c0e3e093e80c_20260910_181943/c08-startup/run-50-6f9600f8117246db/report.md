## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器启动时尝试分配 256Mi 内存，远超 64Mi 的资源限制，触发 Linux OOM Killer 强制终止容器，导致 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff restarting failed container app` (x624) | 直接表现容器崩溃后的剧烈重启行为 |
| 2 | K8s State | Kubernetes | `last_terminated_reason=OOMKilled`, `exit_code=137` | 核心证据：明确指出容器因超内存被内核杀掉 |
| 3 | K8s Config | Kubernetes | `memory request=8Mi`, `memory limit=64Mi` | 边界条件：证实当前资源限制为 64Mi |
| 4 | Logging | Elasticsearch | `startup allocation 256Mi` | 核心证据：提供超内存行为的根本起因 |
| 5 | Metrics | Prometheus | `kube_pod_container_status_last_terminated_reason=1 (OOMKilled)` | 交叉印证：Prometheus 指标与 K8s OOMKilled 状态一致 |

**证据关联性说明：**
- 证据 4 (256Mi 需求) 与证据 3 (64Mi 限制) 构成直接的因果冲突。
- 证据 2 (OOMKilled/137) 是上述冲突在 Kubernetes 维度的直接执行结果。
- 证据 5 (Metric OOMKilled=1) 作为独立指标源，确认了证据 2 的真实性。

## 🎯 根因分析 · g1

### 因果链

```text
App 尝试分配 256Mi 内存 (日志证据) → 超过 64Mi 的 Pod 内存限制 (K8s配置证据) → 触发 Linux OOM Killer 杀死容器 (状态证据) → 容器反复崩溃并进入 CrashLoopBackOff (事件证据)
```

### 根因结论

已确认根因为**应用启动时内存需求（256Mi）显著超过 Pod 资源限制（64Mi）**。

- **启动异常与崩溃**：日志显示应用启动时尝试分配 `256Mi` 内存，这远超了 K8s 配置中设定的 `64Mi` 硬性限制（`fact-1746838a56ac`），导致容器进程被 Linux OOM Killer 强制终止（`fact-4150b06e011f`，`fact-517a4581e694`）。
- **持续重启**：由于 Pod 配置未更新，该内存限制冲突未被解除，导致容器启动后立即被杀，引发 K8s 的指数退避重启机制，当前表现为 `CrashLoopBackOff`（`fact-ff252a1ea198`，`fact-bbfbe4459f87`）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 19.3s
├─ 并发证据采集: 549.9s
│  └─ g1 aiops-case-v15/workload: 549.9s (Evidence 544.8s, RCA 4.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
