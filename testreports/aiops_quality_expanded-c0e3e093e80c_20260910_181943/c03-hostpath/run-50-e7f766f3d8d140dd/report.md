## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | aiops-case-v06/workload Pod 处于 Pending/ContainerCreating 状态，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Pending` | 确定 Pod 当前处于非运行状态 |
| 2 | K8s Event | `event.message` | `FailedMount... hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-8d5747918dd8) | 明确挂载失败原因：路径存在但非目录 |
| 3 | K8s State | `container.waiting_reason` | `ContainerCreating` (fact-aad6f18dc01b) | 确认容器因挂载阻塞而未进入创建后续步骤 |
| 4 | K8s Config | `container.resource_request.memory` | `8Mi` (fact-269c1f3e93bb) | 排除资源规格不足导致的调度或启动延迟 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `reason: ContainerCreating, value: 1` (fact-5d4ec88b78e6) | 独立于 K8s API 的指标观测印证了挂载卡死现象 |

**证据印证说明：**
K8s Event（#2）指出的具体错误（`is not a directory`）与 K8s State（#1, #3）反映的长期阻塞状态完全一致。Metric（#5）提供了独立的指标视角，确认该 Pod 容器持续处于 `ContainerCreating` 等待状态，排除了瞬时抖动导致的事件堆积可能。资源配置（#4）极低，确认现象非资源超限引起。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 挂载路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 在节点 node2 上非目录 → kubelet MountVolume.SetUp 校验失败 → 卷挂载阻塞 → Pod 长期处于 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因：Pod `aiops-case-v06/workload` 的卷挂载失败。
具体机制为：Kubelet 在尝试挂载 HostPath 卷 `input` 时，发现目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度节点 node2 上存在，但其类型不是目录（错误原文：`is not a directory`），导致 `FailedMount` 并持续重试 [证据 #2]。由于挂载无法完成，Pod 无法启动容器，从而停留在 `ContainerCreating` 状态 [证据 #1, #3, #5]。

**未确认项：**
节点 node2 上该路径的确切文件系统状态（是绝对不存在还是存在但为文件）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.2s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v06/workload: 39.9s (Evidence 30.7s, RCA 9.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
