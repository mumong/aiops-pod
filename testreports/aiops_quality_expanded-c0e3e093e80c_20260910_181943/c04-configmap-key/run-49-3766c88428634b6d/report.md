## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 CreateContainerConfigError 状态，持续 Pending 且未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v11/workload` 状态为 Pending，容器 `app` 等待原因为 `CreateContainerConfigError` | 确认核心故障现象 |
| 2 | K8s State | kubernetes | 容器 `app` 报错：`couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 定位配置缺失的直接原因 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=CreateContainerConfigError) 值为 1 | 独立确认容器因配置错误被拦截 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (container=app) 值为 1，`kube_pod_container_status_restarts_total` 值为 0 | 确认 Pod 长期处于未就绪状态且未发生重试 |

证据 1 与 2 共同指向容器因配置项缺失导致无法创建；证据 3 从 Prometheus 指标角度独立验证了 `CreateContainerConfigError` 状态的持续性，与 K8s 状态完全一致，且重启次数为 0 排除了应用崩溃等运行时故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了 ConfigMap aiops-case-v11/workload-input 中不存在的 key 'unavailable-key' → kubelet 在容器创建前校验失败 → 容器状态设为 CreateContainerConfigError → Pod 处于 Pending 且应用逻辑未执行
```

### 根因结论

已确认根因为 **Pod Spec 定义了引用 ConfigMap `aiops-case-v11/workload-input` 中不存在的 `unavailable-key`**，导致 kubelet 无法完成容器环境配置加载 [证据 #2]。该配置错误直接触发了 `CreateContainerConfigError` 异常 [证据 #1, #3]，使得 Pod 无法进入运行状态。现有证据充分且相互印证，无需进一步补充。

---

## 📊 性能统计

```text
├─ 总耗时: 54.9s
├─ 问题定位: 15.1s
├─ 并发证据采集: 32.8s
│  └─ g1 aiops-case-v11/workload: 32.8s (Evidence 23.4s, RCA 9.3s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
