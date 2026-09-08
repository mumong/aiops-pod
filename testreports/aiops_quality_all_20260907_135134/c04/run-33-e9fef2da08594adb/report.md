## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 Pending 状态，容器等待原因为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出 Pod 启动时无法解析 Secret 中的指定密钥 |
| 2 | K8s State | `Pod Status` | `Pending` (0 restarts) | 确认 Pod 处于等待阶段且未发生重启 |
| 3 | Metric | `Prometheus` | `kube_pod_container_status_waiting_reason` (reason: `CreateContainerConfigError`) | 通过监控数据确认容器处于配置错误等待状态 |

证据 1 的 Kubernetes 事件与证据 3 的监控指标互相印证，共同指向容器因配置错误（ConfigError）而处于等待状态。由于 Pod 无法启动，未产生应用日志与追踪数据，因此诊断完全依赖集群控制面的事实。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺失 key 'unavailable-key' → kubelet 在容器创建阶段无法解析 Secret 键值 → 容器启动失败，状态转为 Waiting: CreateContainerConfigError → Pod 维持在 Pending 状态且不发生重启
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 启动失败是由于 Secret `aiops-case-04/workload-input` 中缺少 Pod 环境变量所需的 key `unavailable-key`（证据 1, 3）。这导致 kubelet 在创建容器时验证失败，进而使 Pod 持续处于 `CreateContainerConfigError` 的等待状态，未发生重启（证据 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.1s
├─ 问题定位: 13.8s
├─ 并发证据采集: 39.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 39.1s (Evidence 33.4s, RCA 5.6s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
