## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器 `app` 因 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接定位根因：指定 Secret Key 缺失 |
| 2 | K8s State | Kubernetes | `Pod` 状态为 `Pending`，重启计数为 `0` | 确认故障持续且未发生重试循环 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (Label: `reason=CreateContainerConfigError`) | 指标确认容器处于配置错误状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` (Label: `container=app`) | 佐证容器从未成功启动 |
| 5 | K8s Config | Kubernetes | 容器配置引用：`Secret aiops-case-04/workload-input` | 指明引发错误的资源对象标识 |

**证据分析**
Kubernetes 事件 (证据 #1) 提供了最直接的文本证据，确认了 `kubelet` 因找不到 Secret 键值而对容器初始化失败；Metric (证据 #3, #4) 从指标维度印证了该状态（`CreateContainerConfigError`）的持续存在且无重启行为，两者完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 Secret Key (unavailable-key) → Kubelet 解析环境变量失败 → 容器处于 CreateContainerConfigError 状态 → Pod 维持在 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器 `app` 在配置环境变量时，引用了 Secret `aiops-case-04/workload-input` 中实际并不存在的键 `unavailable-key`（证据 #1）。

这一配置错误导致 `kubelet` 无法完成容器创建前的配置步骤，进而使容器停留在 `CreateContainerConfigError` 状态（证据 #3），表现为 Pod 一直处于 `Pending` 且从未启动过（证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 56.7s
├─ 并发证据采集: 23.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 23.8s (Evidence 16.1s, RCA 7.6s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
