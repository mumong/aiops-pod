## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: Pending | 确认 Pod 未能成功启动进入运行状态 |
| 2 | K8s State | kubernetes | container.waiting_reason: CreateContainerConfigError | 确认容器处于配置注入失败的状态 |
| 3 | K8s State | kubernetes | container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 直接指出缺少特定的 Secret 键值 |
| 4 | K8s Event | kubernetes | kubelet 报告错误事件 | 佐证容器引擎在启动阶段遭遇配置异常 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason=1 (reason: CreateContainerConfigError) | 指标确认集群中该 Pod 确实处于配置错误状态 |

证据 3 提供了明确的错误原文，直接解释了证据 2 和证据 1 中的等待和挂起状态。证据 5 通过监控指标独立验证了该 Pod 确实存在且处于 `CreateContainerConfigError` 状态，与 K8s 状态事实一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 模板引用 'aiops-case-04/workload-input' Secret 中的 'unavailable-key' → kubelet 注入配置失败 → 容器引擎报错 CreateContainerConfigError → Pod 处于 Pending/Waiting 状态
```

### 根因结论

已确认根因为：Pod 模板中引用的 Secret `aiops-case-04/workload-input` 中缺少所需的 `unavailable-key` 键值。

证据 3 中的 K8s 等待消息明确指出 `couldn't find key unavailable-key`，这直接证明了 Secret 配置不匹配是导致 Pod 无法启动并进入 `CreateContainerConfigError` 状态的原因。

---

## 📊 性能统计

```text
├─ 总耗时: 48.7s
├─ 问题定位: 17.6s
├─ 并发证据采集: 24.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 24.5s (Evidence 18.4s, RCA 6.0s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
