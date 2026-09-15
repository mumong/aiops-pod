## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod `workload` 的 Volume 配置错误，引用了 ConfigMap `workload-input` 中不存在的 Key `unavailable-key`，导致 kubelet 挂载失败，Pod 卡在 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount: configmap references non-existent config key: unavailable-key` (fact-4e7933b9d96f) | 确认挂载失败的具体原因为引用了 ConfigMap 中不存在的 Key |
| 2 | K8s State | Kubernetes | Pod Phase `Pending`, Condition `ContainersReady=False` (fact-66df1d9f83ac, fact-54d9357ffd33) | 确认 Pod 当前处于不可用的挂起状态 |
| 3 | K8s State | Kubernetes | Container Waiting Reason `ContainerCreating` (fact-033759a2c9f2) | 确认容器未启动，处于预启动阶段 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 (fact-a2e093e17674) | 验证了容器状态指标与 K8s 事件描述一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-24e224a9fd0a) | 排除容器运行期异常重启或崩溃 |

证据表明 Pod 未能通过初始化阶段的卷挂载检查。Kubernetes 事件明确指向了配置错误（引用不存在的 ConfigMap Key），而 Metrics 的 0 重启计数和 `ContainerCreating` 状态进一步证实问题处于启动前阶段，未进入运行期。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `workload-input` 缺少 Key `unavailable-key` → 容器卷挂载检查失败 → Pod 状态卡在 `ContainerCreating` → 应用服务不可用
```

### 根因结论

已确认的根因是 **Pod `workload` 的 Volume 配置错误**。
Pod 定义中引用了 ConfigMap `workload-input` 中的 `unavailable-key`，但该 Key 实际不存在。这一配置错误导致 kubelet 在挂载卷阶段失败，进而使 Pod 无法启动（状态卡在 `ContainerCreating`，Phase 为 `Pending`）。关键证据为 K8s Event 中的 `FailedMount` 报错（事实 1）以及确认该状态的 Metrics（事实 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.1s
├─ 问题定位: 18.1s
├─ 并发证据采集: 32.9s
│  └─ g1 aiops-case-v05/workload: 32.9s (Evidence 27.6s, RCA 5.2s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed, pod-imagepull-failed, pod-config-error
