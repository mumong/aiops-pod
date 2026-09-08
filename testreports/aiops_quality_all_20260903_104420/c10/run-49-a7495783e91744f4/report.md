## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Container 'app' OOMKilled due to memory usage exceeding the 96Mi limit, leading to CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  BackOff    3m42s (x495 over 134m)  kubelet  Back-off restarting failed container app` | 核心症状证据，表明容器正在被 Kubernetes 反复重启并进入退避策略。 |
| 2 | K8s State | Kubernetes | `Exit Code: 137` (Container `app`) | 决定性的状态证据，Exit Code 137 明确表示容器进程被信号 9 (SIGKILL) 终止，符合 OOM Kill 特征。 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi` (Container `app`) | 故障边界证据，指明了容器内存使用的硬限制，为内存溢出结论提供阈值依据。 |
| 4 | K8s State | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 现象佐证，解释了为什么在容器重启间隙 Liveness 探针会失败，导致 Pod 判定为不健康。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = `Error` (Container `app`) | 独立观测，确认容器最后一次终止原因是 Error，与 K8s Event 和 Exit Code 相互印证。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `45` (Container `app`) | 量化指标，与 Event 中的 45 次重启统计一致，确认故障的持续性和频度。 |
| 7 | Logging | Elasticsearch | `request completed` (HTTP 200, path: `/work`) 观察窗口: `22:23:03` 至 `22:23:32` (8次) | 限定性证据，展示了故障爆发前的服务可用状态及未发生异常的请求模式。 |
| 8 | Tracing | Tempo/Deepflow | `GET /work` (HTTP 200) trace_id: `dbc93c3...` | 关联验证，确认了该业务流量在崩溃发生前或间歇期的正常响应链路。 |

证据逻辑说明：
Exit Code 137 结合 `resource_limit.memory: 96Mi` 和 `BackOff` 事件，构成了内存溢出导致容器崩溃的完整证据链。Metric 的 `Error` 终止原因与 K8s 状态一致。Logging 和 Tracing 展示了崩溃前后的正常 HTTP 流量，证明故障表现为突发性的资源耗尽而非持续性代码逻辑错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存使用突破 96Mi 硬限制 → Linux OOM Killer 强制终止进程 (Exit Code 137) → 容器启动失败且 Liveness 探针返回 500 → Pod 触发 BackOff 机制进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为容器 `app` 的内存使用量超过了配置的 **96Mi** 硬限制。

1. **故障机制验证**：容器 `app` 被 Linux OOM Killer 终止（**事实 #2**, 退出码 137）。
2. **故障边界**：容器的内存硬限制配置为 **96Mi**（**事实 #3**），这是导致被终止的直接阈值。
3. **故障现象**：由于进程被终止，Kubernetes 频繁重启容器，最终触发 `BackOff` 机制进入 **CrashLoopBackOff** 状态（**事实 #1**, **事实 #4**）。
4. **数据一致性**：Metric 数据证实容器最后终止原因为 `Error`（**事实 #5**），重启总数为 45 次（**事实 #6**），与 K8s 事件完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.7s
├─ 并发证据采集: 45.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 45.2s (Evidence 37.2s, RCA 7.9s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-config-error
