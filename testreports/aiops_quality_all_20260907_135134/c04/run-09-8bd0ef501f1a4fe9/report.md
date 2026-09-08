## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 因 CreateContainerConfigError 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet Event | `Failed`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接定位挂载失败的根因：Secret 中缺少引用的 Key |
| 2 | K8s State | kubelet State | `container.waiting_reason`: `CreateContainerConfigError` | 描述 Pod 当前不可用的确切机制 |
| 3 | K8s Config | Pod Spec | `container.resource_request.cpu`: `5m`; `container.resource_limit.memory`: `32Mi` | 排除因资源配置不当导致 Pod 无法调度的可能 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason: `CreateContainerConfigError`) | 独立验证容器一直处于等待状态，确认失败未随时间改变 |

证据内容自洽：Kubelet 事件明确指出了 `workload-input` Secret 中缺失 `unavailable-key`（#1），这与容器处于 `CreateContainerConfigError` 状态的事实（#2）完全吻合。Metric 数据（#4）进一步确认了这种配置错误导致的失败状态在观测时点仍然持续存在，未发生自愈。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'workload-input' 中缺失键 'unavailable-key' → Pod 容器配置引用了该不存在的键 → kubelet 执行 CreateContainerConfig 失败 → Pod 处于 Pending 状态并报错 CreateContainerConfigError
```

### 根因结论

已确认的根因是 Pod 配置引用了不存在于 Secret 中的 Key（`workload-input/unavailable-key`），这直接导致 kubelet 在挂载配置阶段失败，表现为容器处于 `CreateContainerConfigError` 状态。该结论由 kubelet 事件（#1）和 K8s 状态（#2）相互印证，且 Metric 数据（#4）佐证了异常状态的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.8s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 40.1s (Evidence 30.5s, RCA 9.6s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
