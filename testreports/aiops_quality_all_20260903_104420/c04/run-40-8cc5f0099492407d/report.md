## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `waiting_reason`: `CreateContainerConfigError` (`fact-b1618a02a90c`) | 直接确认容器启动失败的根本状态。 |
| 2 | K8s State | `kubernetes` | `waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (`fact-d0a1e970e6f2`) | 明确给出导致创建配置失败的精确缺失字段名称及目标资源。 |
| 3 | K8s Event | `kubernetes` | `Normal Pulled ... Container image ... already present on machine` (349次 over 78m) (`fact-8c4e49d9c0ea`) | 证明镜像拉取及底层环境正常，排除镜像故障，锁定配置阶段异常。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1 (reason=`CreateContainerConfigError`) (`fact-6c1b0175edab`) | 通过 Prometheus 指标独立印证 K8s API 返回的状态。 |

**证据说明：**
1. **K8s API 与指标的一致性**：事实 #2 提供了具体的报错原因（Missing Secret Key），事实 #1 确认了该原因的宏观状态。事实 #4 通过监控指标交叉验证了 Pod 处于相同的等待原因状态。
2. **现象排除**：事实 #3 显示容器镜像长期存在且拉取成功（连续 349 次），结合 `restart_count` 为 0 的事实，证明 Pod 卡在启动前阶段，排除了应用逻辑崩溃或资源耗尽导致的问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret 'workload-input' 中的 key 'unavailable-key' → 缺少该 key 导致 Secret 解析/注入失败 → kubelet 抛出 CreateContainerConfigError 阻止容器启动 → Pod 持续处于 Pending/NotReady 状态
```

### 根因结论

**已确认根因：Pod 配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。**

证据显示，Pod 在启动配置阶段，因无法在目标 Secret 中找到所需的 `unavailable-key` 字段（见事实 #2），直接触发了 `CreateContainerConfigError`（见事实 #1、#4）。由于容器未能进入运行态，未产生有效的应用日志或追踪数据，但这并不影响对配置错误的确定性结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 14.5s
├─ 并发证据采集: 103.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 103.6s (Evidence 94.7s, RCA 8.7s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
