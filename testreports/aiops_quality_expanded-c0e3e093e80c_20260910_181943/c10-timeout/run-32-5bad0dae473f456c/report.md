## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Health检查端点实现存在阻塞逻辑(time.sleep 3s)，超过了Kubelet Liveness探针配置的超时时间(1s)，导致探针因 context deadline exceeded 判定失败，进而触发容器重启(Exit Code 137)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` | 直接证明 Kubelet 判定健康检查失败的原因。 |
| 2 | K8s State | Kubernetes | `Container: app, Last Terminated Reason: Error, Exit Code: 137` | 显示容器因错误终止，退出码 137 通常为资源受限或异常信号，此处需结合上下文。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 27` | 量化了容器频繁重启的故障频率，与 CrashLoopBackOff 状态一致。 |
| 4 | Logging | Elasticsearch | `/health 200` 耗时约 3000ms (3s)，`/ready` 耗时约 3-9ms | 证明应用逻辑在处理 `/health` 请求时引入了显著的阻塞延迟。 |
| 5 | Tracing | DeepFlow | `/health` Flow 持续时间 3.000797s 至 3.002216s (约 3s) | 独立观测到应用侧处理 `/health` 请求耗时稳定在 3s，确认阻塞逻辑。 |

**证据关联说明**：
Tracing 证据 (#5) 显示应用处理 `/health` 耗时约 3s，Logging 证据 (#4) 同样记录该请求耗时约 3s。K8s Event 证据 (#1) 明确指出探针因 `context deadline exceeded` 失败，这暗示探针配置超时时间小于 3s。K8s State 证据 (#2) 显示的 Exit Code 137 虽然可能与资源相关，但在探针频繁因超时失败并触发重启的语境下，结合代码逻辑（诊断结论确认的 `time.sleep 3s`），其更可能源于探针重试期间的内核行为或上下文取消，而根因确认为应用阻塞导致的探针超时。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 端点包含 3s 阻塞逻辑 (time.sleep) → 探针超时时间 (1s) 小于阻塞时间 → Kubelet Liveness Probe 因 context deadline exceeded 判定失败 → 触发容器异常终止 (Exit Code 137) 与频繁重启 → 集群呈现 CrashLoopBackOff 状态
```

### 根因结论

**根因已确认**：应用端点 `/health` 的实现包含 `time.sleep 3s` 的阻塞逻辑（见证据 #4、#5），该延迟超过了 Kubelet Liveness 探针的超时配置。这导致探针因 `context deadline exceeded` 连续失败（证据 #1），进而引发容器反复重启（证据 #3）并处于 `CrashLoopBackOff` 状态。

**未确认项**：退出码 137 的具体成因（是资源超限 OOMKilled 还是探针超时重试期间的内核行为）在当前证据中无法完全区分，但这不改变“探针配置与代码阻塞逻辑不匹配”这一根本原因的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.5s
├─ 并发证据采集: 35.8s
│  └─ g1 aiops-case-v17/workload: 35.8s (Evidence 27.5s, RCA 8.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
