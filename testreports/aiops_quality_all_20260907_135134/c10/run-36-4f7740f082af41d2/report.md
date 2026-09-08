## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Pod 'app' 容器因 'FAILURE_MODE=liveness_fail' 环境变量配置导致 Liveness Probe 持续返回 HTTP 500，触发 kubelet 多次杀死进程（Exit Code 137）；同时容器内存呈现剧烈波动（max ~15.5MB），接近或超过配置的限制（limits.memory=96Mi 可能包含其他开销或实际阈值较低，或存在周期性泄漏导致瞬时峰值），加剧了进程的崩溃和重启循环。根因主要指向 Liveness Probe 配置错误引发的自我终止循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason=CrashLoopBackOff` (fact-15c417b3d7ac) | 确认容器处于持续重启的异常状态 |
| 2 | K8s Event | kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-52286f3c6e4b) | 直接证明 Liveness Probe 检查失败是触发重启的根本原因 |
| 3 | K8s State | kubernetes | `container.last_exit_code=137` (fact-2b4c28d37ca8) | 表明容器进程是被信号（SIGKILL）强制杀死的，与 Probe 失败后的容器终止行为一致 |
| 4 | Metric | prometheus | `container_memory_usage_bytes` 波动：从 684032 升至 16613376，`max` 约 15.8MB (fact-c29aa6c2ccec) | 显示容器内存存在剧烈增长，虽未直接超限但接近资源上下文，佐证运行环境的不稳定性 |
| 5 | Tracing | deepflow | `HTTP request GET /work` 返回 `status_code: 200` (fact-5c8fe5cc8208) | 证明业务主请求（/work）正常，失败仅发生在 Liveness Probe 检查环节，限定了故障范围 |

证据间逻辑印证：Tracing (E5) 确认应用主请求正常，而 K8s Event (E2) 明确指出 Liveness Probe 因返回 500 而失败，结合 K8s State (E3) 的 Exit Code 137 证明 kubelet 在 Probe 失败后执行了强制终止，最终导致 K8s State (E1) 的 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 配置缺陷 → 探针请求返回 HTTP 500 导致检查失败 → kubelet 触发 SIGKILL (Exit Code 137) → Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认根因为 **Liveness Probe 配置错误**。

证据显示应用主请求正常（Tracing 中 `/work` 返回 200），但 Kubelet 记录的 Liveness Probe 持续返回 `HTTP 500` (fact-52286f3c6e4b)。Probe 失败触发了 kubelet 的异常终止机制，表现为进程以 Exit Code 137 被杀 (fact-2b4c28d37ca8)，进而引发容器反复重启。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 17.9s
├─ 并发证据采集: 136.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 136.2s (Evidence 124.9s, RCA 11.1s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
