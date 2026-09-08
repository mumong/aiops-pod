## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，Container 'app' 报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (container: `app`) | 确认容器因配置注入失败无法启动 |
| 2 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供精确的错误定位：Secret 中缺失指定 Key |
| 3 | K8s Event | kubernetes | `Failed  38m (x12 over 40m) kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认 kubelet 尝试挂载失败的状态持续存在 |
| 4 | K8s State | kubernetes | `pod.status`: `Pending`; `ContainersReady`: `False` | 证实 Pod 因上述原因处于阻塞状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1 (label: `reason=CreateContainerConfigError`), 样本数 1 | 从指标侧印证容器处于因配置报错导致的等待状态 |
| 6 | K8s Config | kubernetes | `resource_limit.memory`: `32Mi`, `resource_request.memory`: `8Mi`, `cpu`: `5m` | 确认资源规格配置正常，排除资源不足导致的配置注入失败 |

上述证据相互印证：Kubernetes 事件与状态直接指出了具体的缺失 Key，Metric 数据在宏观上确认了该状态的存在。由于容器未能启动（无重启计数，仅 0 次），Logging 和 Tracing 维度因物理限制无法产生诊断数据，属于预期结果。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 缺失 Pod 所需的 Key 'unavailable-key' → kubelet 解析 Secret 挂载配置失败 → Container 'app' 配置注入中断，报错 CreateContainerConfigError → Pod 保持 Pending 状态，持续重试挂载直至超时或退避
```

### 根因结论

已确认根因：Pod 配置错误引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`。

证据编号 2 和 3 明确指出 `kubelet` 在尝试挂载 Secret 时找不到 `unavailable-key`，导致容器启动被阻断，抛出 `CreateContainerConfigError`。指标数据（编号 5）佐证了这一状态持续存在。现有证据链条完整，足以解释当前现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.3s
├─ 并发证据采集: 45.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 45.4s (Evidence 36.2s, RCA 9.1s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
