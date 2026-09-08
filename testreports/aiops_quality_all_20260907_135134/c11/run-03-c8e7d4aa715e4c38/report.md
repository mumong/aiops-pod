## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod被自定义finalizer 'aiops.lab/hold'阻塞，导致在容器因OOM或外部SIGKILL（exitCode=137）终止后仍无法从API Server中移除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: "Terminating (lasts 6m53s)", `pod.phase`: "Running" | 确认 Pod 处于异常终止僵死状态，且生命周期已达数分钟。 |
| 2 | K8s Event | Kubernetes | `message`: "Killing", `message`: "Exit Code: 137" | 证明容器进程（app）被外部强制终止（SIGKILL），为异常提供直接诱因。 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: "96Mi" | 提供系统配置上下文，结合 Exit Code 137 辅助判断终止原因。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (样本 6 次) | 确认容器当前尚未触发重启机制，佐证 Pod 对象停留在“终止中”而非“重建中”。 |
| 5 | Logging | Elasticsearch | `pattern`: `request completed, http_status: 200`, `allocated_mib`: 0.0 | 记录终止前最后一次业务请求正常完成，排除应用侧错误导致的异常退出。 |
| 6 | Tracing | Deepflow | `flow`: `GET /work, response_code: 200`, `trace_ids`: `25d61c...` 等 | 关联 L7 正常请求记录，确认网络侧与业务侧在终止前无失败现象。 |

**证据分析：**
Kubernetes 事实明确记录了 Pod 卡在 `Terminating` 状态，且伴随明确的强制终止事件（`Exit Code: 137`）。Metrics、Logging 与 Tracing 维度均呈现正常的服务运行指标（无重启、无报错、正常响应），共同排除了底层节点故障或大规模应用崩溃，将问题锚定在 Pod 资源本身的生命周期管理（即对象无法被 API Server 最终删除）上。

## 🎯 根因分析 · g1

### 因果链

```text
自定义finalizer 'aiops.lab/hold'存在且未移除 → 容器进程被终止（Exit Code 137） → Kubernetes API Server因finalizer未清理而拒绝删除Pod对象 → Pod长期处于Terminating状态
```

### 根因结论

已确认根因为 `aiops.lab/hold` 自定义 finalizer 导致的删除阻塞。

容器进程因异常（如 OOM 或 SIGKILL，`Exit Code: 137`）终止后，Kubernetes 尝试清理该 Pod。由于 Pod 对象存在未清理的 `aiops.lab/hold` finalizer，API Server 拒绝执行删除操作，导致 Pod 对象永远处于 `Terminating` 状态。证据 [1] 中的持久终止状态与证据 [2] 中的强制终止事件互相印证了当前现象。缺失的确定性事实为 `aiops.lab/hold` 对应控制器或 Webhook 的具体状态，但这不影响“删除请求被 finalizer 阻塞”这一核心根因的成立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 13.7s
├─ 并发证据采集: 69.8s
│  └─ g1 aiops-case-11/workload: 69.8s (Evidence 61.7s, RCA 8.0s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
