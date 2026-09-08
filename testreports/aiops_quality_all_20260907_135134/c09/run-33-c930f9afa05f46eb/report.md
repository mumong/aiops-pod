## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用依赖项不可用导致就绪探针持续返回 HTTP 503，使容器被标记为未就绪（ContainersNotReady）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning Unhealthy 90s (x1350 over 66m) ... Readiness probe failed: HTTP probe failed with statuscode: 503` ([fact-1b58c10773df](fact-1b58c10773df)) | 确认应用层面的 `ReadinessProbe` 连续 66 分钟返回 503，导致探针持续失败。 |
| 2 | K8s State | `Pod Condition` | `ContainersReady: False, Ready: False, reason: ContainersNotReady` ([fact-72b813d10923](fact-72b813d10923)) | 证实 Pod 因容器就绪状态不满足而被 K8s 标记为未就绪。 |
| 3 | Logging | `elasticsearch` | 错误日志模式 `dependency unavailable`，HTTP `status: 503`，路径 `/work`，11 次发生，时间范围 `19:54:22 - 19:58:15` ([fact-27671913ed85](fact-27671913ed85)) | 定位应用代码在 `/work` 接口返回 503 的具体业务原因为“依赖项不可用”。 |
| 4 | Tracing | `tempo + deepflow` | HTTP `GET /work` 返回 503，`src_ip: 172.16.104.55`, `dst_ip: 172.16.104.35`，11 次发生 ([fact-3a388dd41dc4](fact-3a388dd41dc4)) | 关联探针来源 IP 与业务端点，证明是外部探针请求触发了此 503 错误。 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_ready: 0` ([fact-df9c913c00d6](fact-df9c913c00d6)) | 外部指标确认容器就绪状态持续为 0，与 Pod Condition 状态一致。 |
| 6 | Metric | `prometheus` | `container_memory_working_set_bytes: 15429632` (约 14.7 MiB) ([fact-719194f2b2c3](fact-719194f2b2c3)) | 内存使用量远低于配置上限 96Mi ([fact-95193e9e30d1](fact-95193e9e30d1))，排除了资源耗尽导致应用崩溃的可能。 |

**证据说明：**
Kubernetes 事件与指标一致确认了 Pod 因 `ContainersNotReady` 而处于非就绪状态；应用日志揭示了业务端点 `/work` 返回 503 的确切原因为“依赖项不可用”；追踪数据证实了这是针对该 Pod 探针端点的请求结果；资源指标排除了 OOM 等基础设施问题，所有证据均指向应用自身或其依赖关系。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖项不可用 → /work 接口返回 HTTP 503 → ReadinessProbe 持续检查失败 → Pod 被标记为 ContainersNotReady (Ready: False)
```

### 根因结论

已确认根因为**应用依赖项不可用**。

应用部署的 `workload-5f4fb9ff45-7b77l` 在 `ReadinessProbe` 探测路径 `/work` 上持续返回 HTTP 503。根据日志证据 ([fact-27671913ed85](fact-27671913ed85))，该接口 503 状态的具体业务语义为“依赖项不可用”。由于探针持续失败，Kubernetes 无法将 Pod 标记为 `Ready`（见 [fact-72b813d10923](fact-72b813d10923) 与 [fact-df9c913c00d6](fact-df9c913c00d6)）。资源监控显示内存与 CPU 使用正常，排除了资源超限导致的进程异常，确认为应用逻辑/依赖故障。

---

## 📊 性能统计

```text
├─ 总耗时: 4.9m
├─ 问题定位: 20.3s
├─ 并发证据采集: 256.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 256.9s (Evidence 250.9s, RCA 5.9s)
└─ 汇总总结: 15.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
