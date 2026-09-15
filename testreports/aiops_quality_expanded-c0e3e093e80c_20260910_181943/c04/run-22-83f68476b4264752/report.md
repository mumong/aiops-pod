## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 核心直接原因，明确指出 Secret 缺失特定 Key |
| 2 | K8s State | Container | `waiting_reason: CreateContainerConfigError` | 确认容器因配置错误无法启动 |
| 3 | K8s State | Pod | `phase: Pending`, `ContainersNotReady` | 确认 Pod 因配置问题停滞在 Pending 状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 从监控维度印证了容器处于配置错误等待状态 |

**证据说明：**
1. K8s Event (#1) 与 K8s State (#2) 形成闭环，明确了故障类型为“创建容器配置错误”，且具体原因为 Secret 中缺少 `unavailable-key`。
2. Metric (#4) 从时间序列监控角度独立证实了容器处于 `CreateContainerConfigError` 状态，与 K8s 事件原因一致。
3. Logging/Tracing 维度标记为 `not_applicable`，符合容器未成功启动无法生成业务日志的物理事实。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 缺失 key 'unavailable-key' 
→ kubelet 拉取容器配置失败 (CreateContainerConfigError) 
→ Pod 状态维持在 Pending，容器无法启动 
→ 应用服务不可用
```

### 根因结论

已确认根因为：**Pod 的 Volume 引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 key 在 Secret 中不存在**。

该事实由以下证据共同支撑：
- K8s Event `fact-844376b32fc7` 明确报告了找不到指定 key 的错误。
- Container `fact-3a9cc689833f` 和 Metric `fact-b8729e8386b3` 均一致显示 `CreateContainerConfigError` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 20.3s
├─ 并发证据采集: 554.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 554.8s (Evidence 548.7s, RCA 6.0s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
