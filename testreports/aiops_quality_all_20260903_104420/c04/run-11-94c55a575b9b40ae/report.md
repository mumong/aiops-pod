## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 Pending 状态，持续报 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-01f07fc89e12` | 容器 `app` 等待状态信息：`couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 核心证据：明确指出挂载的 Secret 中缺少预期 Key |
| 2 | K8s State | `fact-6bbb32b99e81` | 容器 `app` 等待原因：`CreateContainerConfigError` | 确认故障机制为配置加载失败，直接导致容器无法启动 |
| 3 | K8s Event | `fact-5a4e032fc5cd` | Warning 事件 `Failed` 持续 24 分钟，内容重复 `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认为持续性故障，非瞬时抖动 |
| 4 | Metric | `fact-a75bd8dbc28f` | Prometheus 指标 `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1 | 外部监控确认状态，排除 K8s API 同步延迟导致的误报 |

上述证据形成完整闭环：`K8s State` 的 `CreateContainerConfigError` 状态与 `K8s Event` 的持续报错直接对应，且错误原因具体指向 Secret 的 `unavailable-key` 缺失；`Metric` 独立确认了容器正处于该等待状态，佐证了故障的客观性。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 仅包含 'available-key'，缺失 'unavailable-key' → 
Pod 模板配置引用了不存在的 'unavailable-key' → 
kubelet 无法解析 Secret key，创建容器时抛出配置错误 → 
Pod 处于 Pending 状态，状态码 CreateContainerConfigError
```

### 根因结论

已确认的根因是 Pod 的 volume 或 env 引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`（该 Secret 中实际仅包含 `available-key`）。

这一配置错误导致 kubelet 在尝试挂载 Secret 时无法找到所需 key，从而触发 `CreateContainerConfigError` 机制，使得容器 `app` 无法初始化，Pod 始终处于 Pending 状态。该结论由 K8s 原生状态（`CreateContainerConfigError`）及明确提示缺失 Key 的等待信息直接支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.4s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 44.5s (Evidence 34.8s, RCA 9.5s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
