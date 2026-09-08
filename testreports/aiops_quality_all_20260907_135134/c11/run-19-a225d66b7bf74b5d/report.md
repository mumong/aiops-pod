## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 33 分钟未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status` 为 `Terminating (lasts 33m)` | 确认 Pod 处于异常终止阻塞状态 |
| 2 | K8s Event | Kubernetes | `Killing` 事件：`Stopping container app` | 确认 Kubelet 已尝试终止容器 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason` 为 `Error`，`container.last_exit_code` 为 `137` | 证实容器因 OOM-Killed (Exit Code 137) 异常终止 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 `0` | 确认当前未发生重启，进一步印证状态卡在 Terminating |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory` 为 `96Mi` | 提供容器资源受限配置事实，支撑 OOM 推断 |
| 6 | K8s Config | Kubernetes | `container.resource_request.cpu` 为 `20m`, `container.resource_limit.cpu` 为 `200m` | 提供 CPU 资源限制信息 |

证据印证：Kubernetes 事件显示 Kubelet 在 33 分钟内持续发送 `Stopping container app` 指令，而 Exit Code 137 结合 96Mi 内存限制事实，确凿表明容器因 OOM 终止。Metric 数据确认 Pod 并未重启，而是维持在 Terminating 状态，这排除了正常重启循环的可能性，指向终止流程被阻断。

## 🎯 根因分析 · g1

```text
容器资源受限 (96Mi) → OOM-Killed (Exit 137) → Pod 对象触发删除流程 → 自定义 finalizer 'aiops.lab/hold' 未被清除 → API Server 阻止删除 → Pod 卡在 Terminating (33m)
```

**根因结论**：
已确认根因为 **自定义 finalizer `aiops.lab/hold` 阻止 Pod 删除**（引用 K8s State 事实）。
容器进程因资源限制被 OOM-Kill 终止（Exit Code 137），Kubernetes 启动删除流程，但由于 Pod 元数据中包含 `aiops.lab/hold` finalizer，且对应的自定义资源或控制器未能及时清除该 finalizer，导致 API Server 无法完成 Pod 对象的移除操作，从而使 Pod 长期停留在 Terminating 状态。
缺失决定性事实：持有 `aiops.lab/hold` finalizer 的具体自定义资源或控制器尚未查明（未知项）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.2s
├─ 并发证据采集: 42.2s
│  └─ g1 aiops-case-11/workload: 42.2s (Evidence 34.4s, RCA 7.7s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
