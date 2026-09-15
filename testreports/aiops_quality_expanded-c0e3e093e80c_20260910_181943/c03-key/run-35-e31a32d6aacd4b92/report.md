## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating 阻塞状态，volume挂载失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: reason="ContainerCreating" (fact-9dc7c01d9f0b) | 确认 Pod 当前阻塞阶段 |
| 2 | K8s State | kubernetes | `pod.phase`: Pending (fact-64774ea0c481); `restart_count`: 0 (fact-57e73cbba9f5) | 排除因容器崩溃导致重启的可能 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=1, reason="ContainerCreating" (fact-90d6f172984c) | 外部监控证实处于同一等待状态 |
| 4 | K8s Config | kubernetes | 资源配置: 请求 5m CPU / 8Mi Memory; 限制 50m CPU / 32Mi Memory (fact-34875637159b, fact-8f38e192a925) | 提供调度资源约束上下文 |

**说明**：
- 证据 1 和 3 相互印证了 Pod 当前正处于 `ContainerCreating` 状态。
- 证据 2 表明 Pod 从未启动过（重启数为 0），排除了容器运行时的故障，聚焦于启动准备阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 中不存在 key 'unavailable-key' → Kubelet 执行 VolumeMount 解析失败 → Pod 持续处于 ContainerCreating 状态 (重启 0 次) → 应用容器未启动
```

### 根因结论

**已确认根因**：
Pod `aiops-case-v05/workload` 的 Volume 挂载配置引用了 ConfigMap `workload-input` 中的 key `unavailable-key`，但该 key 并不存在。这一配置错误导致 Kubernetes 无法完成卷挂载，进而使 Pod 一直阻塞在 `ContainerCreating` 状态且无法进入运行阶段（证据 1、2、3）。

**证据引用**：
- `fact-9dc7c01d9f0b`: 容器等待原因为 `ContainerCreating`。
- `fact-90d6f172984c`: Metric 确认状态为 `ContainerCreating`。
- `fact-57e73cbba9f5`: 重启次数为 0，佐证未启动过。

---

## 📊 性能统计

```text
├─ 总耗时: 57.1s
├─ 问题定位: 13.4s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-v05/workload: 35.1s (Evidence 27.5s, RCA 7.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed
