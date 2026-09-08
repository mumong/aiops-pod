## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 无法启动并持续报 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认 Kubelet 因找不到 Secret Key 拒绝挂载配置 |
| 2 | K8s State | kubernetes | `container.app waiting.message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 直接指向具体的配置缺失项 |
| 3 | K8s State | kubernetes | `container.app waiting.reason: CreateContainerConfigError` | 确认当前处于因配置错误导致的容器启动失败状态 |
| 4 | K8s State | kubernetes | `pod.phase: Pending` | 描述 Pod 当前的整体状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` | 验证了等待状态及具体错误类型（当前值） |

**证据总结**：K8s 事件日志 (`fact-4c7daf17ef07`) 与容器状态消息 (`fact-ac74db26b507`) 互相印证，明确指出 Pod 处于 `CreateContainerConfigError` 状态且直接原因为 Secret `aiops-case-04/workload-input` 中缺少 `unavailable-key`。Metric 数据 (`fact-36bc0dd35bc3`) 从 Prometheus 角度确认了该容器正持续处于 `CreateContainerConfigError` 等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 缺失 key 'unavailable-key' → Kubelet 挂载 Secret 配置失败 → 容器启动被拒绝 (CreateContainerConfigError) → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：
Pod 模板中配置引用的 Secret `aiops-case-04/workload-input` 中不存在 `unavailable-key` 这一 key（事实 `fact-4c7daf17ef07`）。Kubelet 在尝试挂载该 Secret 时因找不到对应 Key 而触发 `CreateContainerConfigError`（事实 `fact-ac74db26b507`、`fact-f67327fb69f0`），导致容器 `app` 无法启动，Pod 停留在 `Pending` 状态（事实 `fact-add01929d32b`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.5s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 43.3s (Evidence 34.7s, RCA 8.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
