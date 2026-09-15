## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating 状态，长时间处于 Pending 阶段，未进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接指出挂载失败的技术原因及目标路径 |
| 2 | K8s State | Kubernetes | `pod.status: Pending` 且 `ContainerCreating` | 确认 Pod 因挂载阻塞处于等待状态 |
| 3 | K8s Config | Kubernetes | Volume `input` 定义使用 `hostPath` 挂载至 `/var/lib/aiops-fixture-unavailable-7f394bef/input` | 提供导致失败的资源定义源头 |
| 4 | K8s Event | Kubernetes | `timed out waiting for the condition` (重复 31 次) | 确认挂载操作经历了长周期的尝试与超时 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 `1` (sample_count=1) | 从监控侧独立确认容器处于挂载创建的等待态 |

**证据综述：**
Kubernetes 事件 `fact-1aac862433e9` 提供了明确的失败原文，直接指向 `hostPath` 路径校验失败；监控数据 `fact-785c033a5061` 与 Pod 状态 `fact-850d8e1d6417` 一致地反映了该 Pod 长期处于 `ContainerCreating` 的等待状态，未进入运行态。事件中的错误信息直接解释了 Pod 状态停滞的原因。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 上 /var/lib/aiops-fixture-unavailable-7f394bef/input 路径不存在或非目录类型 → kubelet 挂载 volume 'input' 失败 (hostPath type check failed) → Pod 状态维持在 ContainerCreating/Pending → 用户可见 Pod 无法启动且无任何应用日志或链路数据
```

### 根因结论

已确认根因为：Pod 定义的 `HostPath` 卷挂载目标路径在调度节点 node2 上不存在或类型不符（事件原文确认 `is not a directory`），导致 `MountVolume.SetUp` 失败。该机制直接阻断了容器的初始化（引用证据 #1）。目前已知该路径在节点上缺失，但导致该路径缺失的具体节点侧原因（如节点配置错误或清理脚本操作）属于未确认环节。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 23.8s
├─ 并发证据采集: 29.0s
│  └─ g1 aiops-case-v06/workload: 29.0s (Evidence 20.8s, RCA 8.1s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
