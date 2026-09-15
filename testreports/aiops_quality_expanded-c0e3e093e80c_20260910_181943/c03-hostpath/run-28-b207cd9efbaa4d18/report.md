## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod `aiops-case-v06/workload` 引用了一个节点 `node2` 上未正确创建的 HostPath 卷 `input`，路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 实际不是目录，导致 kubelet 挂载失败并持续阻塞 Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount`: `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-92f061fbcff9) | 明确根因：指定的 HostPath 路径不存在或类型不符 |
| 2 | K8s State | kubelet | `pod.status`: `Pending` (fact-145ea22d2b27) | 确认 Pod 处于阻塞状态，无法进入运行阶段 |
| 3 | K8s State | kubelet | `pod.condition`: `ContainersReady=False`, reason=`ContainersNotReady` (fact-c92cda7af738) | 确认容器就绪检查失败，无法提供服务 |
| 4 | K8s State | kubelet | `container.waiting_reason`: `ContainerCreating` (fact-a3fc0abd5d12) | 确认容器卡在创建阶段，尚未启动进程 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=`ContainerCreating`) (fact-5134823997ad) | 数值监控印证了 Pod 持续卡在 ContainerCreating 状态 |

证据表明，Pod 因 kubelet 挂载 HostPath 卷失败而阻塞在 Pending 状态，所有等待/非就绪指标均指向同一挂载故障，无资源争用或应用崩溃迹象。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 上路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 实际不是目录 → kubelet HostPath type check failed → Pod 挂载卷 input 失败 → Pod 处于 Pending/ContainerCreating 阻塞状态
```

### 根因结论

已确认根因为 **Pod `aiops-case-v06/workload` 引用的 HostPath 卷 `input` 路径配置错误**（事实 `fact-92f061fbcff9` 明确指出 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是目录）。该配置缺陷直接导致 kubelet 挂载失败，进而使得 Pod 持续处于 Pending 状态且无法启动容器。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.1s
├─ 并发证据采集: 43.7s
│  └─ g1 aiops-case-v06/workload: 43.7s (Evidence 37.9s, RCA 5.6s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed, pod-config-error
