## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | node2 上的 HostPath 挂载点 /var/lib/aiops-fixture-unavailable-7f394bef/input 缺失或类型不正确 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount`: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | **直接证据**：明确指出了挂载失败的具体原因是目标路径类型不符合预期 |
| 2 | K8s Event | kubelet | `FailedMount`: `Unable to attach or mount volumes: unmounted volumes=[input]` | 确认挂载卷 `input` 被挂载失败，Pod 无法完成初始化 |
| 3 | K8s State | kubelet | `Pod status: Pending`, `ContainerCreating` | 确认 Pod 因挂载问题处于未就绪的阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: `ContainerCreating` | 验证 Pod 持续处于挂载等待阶段，与事件日志吻合 |
| 5 | K8s Config | kubelet | `container.resource_request.memory: 8Mi`, `cpu: 5m` | 排除因资源请求过高导致调度或启动失败的干扰 |

K8s Event 提供了挂载失败的精确原因（目录类型错误），Metric 数据佐证了 Pod 长期处于 `ContainerCreating` 等待状态，两者共同确认了故障点在于 HostPath 挂载环节，而非资源调度或容器内部逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
node2 路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或不是目录 → kubelet 执行卷挂载失败 → Pod 处于 Pending 状态，容器处于 ContainerCreating 等待期 → 应用无法启动
```

### 根因结论

已确认根因为 `node2` 上的 HostPath 挂载点 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 缺失或类型不正确（见证据 #1）。该路径不满足挂载要求，导致 `kubelet` 抛出 `hostPath type check failed` 错误，使 Pod 卡在 `ContainerCreating` 状态（见证据 #2, #3, #4）。

**缺失的决定性事实**：目前证据仅指出了路径类型不符，但未明确路径缺失的具体系统级原因（如目录确实不存在、被删除、或是文件而非目录），因此节点上该目录缺失的具体成因标记为“未确认”。

---

## 📊 性能统计

```text
├─ 总耗时: 44.6s
├─ 问题定位: 16.8s
├─ 并发证据采集: 19.8s
│  └─ g1 aiops-case-v06/workload: 19.8s (Evidence 13.1s, RCA 6.6s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
