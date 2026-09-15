## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh in aiops-case-05 remains in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5dbb5dcd6c-bntfh` Phase: `Pending`; Container `app` Status: `waiting`, Reason: `ContainerCreating`; Condition `ContainersReady`/`Ready`: `False` (ContainersNotReady) | 确认 Pod 卡在容器创建阶段，未进入运行态 |
| 2 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` 当前值为 1 | 辅助确认集群层面容器状态一致为等待创建 |
| 3 | K8s Config | Kubernetes | Resource Requests: CPU `5m`, Memory `8Mi`; Limits: CPU `50m`, Memory `32Mi` | 排除因资源请求过高导致调度或运行时资源不足的可能性 |
| 4 | K8s Config | Kubernetes | `unknowns` 字段明确指出未找到 `NetworkAttachmentDefinition 'unavailable-network'`，状态为 deleted/never created 或 scope error | 直接指向 Multus CNI 依赖缺失，是网络环境异常的关键线索 |

**证据关联说明：**
Kubernetes 的 `ContainerCreating` 状态与 Metrics 指标一致，且资源配额极低，排除了资源压力。核心矛盾点在于 Pod 在启动阶段卡住，结合事实中明确标记的 `NetworkAttachmentDefinition` 缺失信息，表明故障定位在 CNI 插件处理网络附件配置时。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 在 aiops-case-05 命名空间中不存在 → Multus CNI 插件无法解析并配置 Pod 网络接口 (FailedCreatePodSandBox) → 容器接口设置失败，Pod 无法进入 Running 状态 → 现象表现为 Pod 长时间卡在 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因：**Multus CNI 配置依赖缺失导致沙箱创建失败**。
`NetworkAttachmentDefinition` 资源 `unavailable-network` 在目标命名空间中缺失（可能是未创建、已删除或跨命名空间引用错误），导致 Multus 插件在 Pod 调度后初始化网络时阻塞。现有证据充分说明网络附件缺失是造成 Pod 状态卡住的直接原因；至于该定义为何缺失的具体历史原因（如误删或遗漏），因缺乏对应的操作审计日志，暂无法定论，但不影响当前故障的根本判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.5s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 40.1s (Evidence 30.4s, RCA 9.6s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-sandbox-create-failed
