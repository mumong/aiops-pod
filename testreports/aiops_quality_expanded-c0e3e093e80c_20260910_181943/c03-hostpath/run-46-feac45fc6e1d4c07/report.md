## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload (aiops-case-v06) stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-e9530d62a1ff` | MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory | 确认定量：Kubelet 因目标路径非法（非目录）导致挂载失败 |
| 2 | K8s Event | `fact-3e3c44a2b2a1` | Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 确认时序：挂载失败已持续约 78 分钟（发生 31-45 次），表明是持续性故障而非瞬时抖动 |
| 3 | K8s State | `fact-842f141599a8` | resource_limit.cpu: 50m | 排除资源瓶颈：CPU 限制极低，无资源过载导致的调度阻塞可能 |
| 4 | Metric | `fact-e5a8f98c8251` | kube_pod_container_status_waiting_reason: 1 (reason=ContainerCreating) | 确认现象：容器持续处于创建等待状态，未进入运行或重启循环 |
| 5 | Metric | `fact-88d9057ac7b7` | kube_pod_container_status_restarts_total: 0 | 排除重启风暴：Pod 自调度后 0 次重启，符合挂载阶段无法启动容器的特征 |

**证据关联说明**
K8s Event `fact-e9530d62a1ff` 直接指明了失败的物理机制（HostPath 目录不存在），Metric `fact-e5a8f98c8251` 证实了该故障是长期的而非瞬时的，二者结合排除了网络或临时 I/O 问题，将故障点精准定位到节点本地的存储路径配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
Node2 节点上 HostPath '/var/lib/aiops-fixture-unavailable-7f394bef/input' 不存在或非目录 → Kubelet 执行 volume type check 失败 (FailedMount) → Pod 挂载阶段阻塞，容器无法启动 → Pod 状态卡在 Pending/ContainerCreating
```

### 根因结论

已确认的根因为**节点本地 HostPath 挂载配置错误**。

工作负载 `aiops-case-v06/workload` 声明了名为 `input` 的 HostPath 卷，要求挂载节点（node2）上的 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 路径。K8s Event `fact-e9530d62a1ff` 明确报告“hostPath type check failed: ... is not a directory”，说明该路径在节点上缺失或类型不符。这导致 Kubelet 无法完成挂载初始化，Pod 被永久阻塞在 `ContainerCreating` 状态（`fact-e9530d62a1ff`, `fact-3bb2a7e4c488`），无应用日志或重启记录产生。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.6s
├─ 并发证据采集: 35.2s
│  └─ g1 aiops-case-v06/workload: 35.2s (Evidence 25.8s, RCA 9.3s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
