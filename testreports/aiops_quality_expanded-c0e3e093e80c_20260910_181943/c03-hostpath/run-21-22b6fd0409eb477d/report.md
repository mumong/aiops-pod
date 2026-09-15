## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath volume mount point mismatch |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | Ready=False, ContainersNotReady | 确认 Pod 处于非就绪状态 |
| 2 | K8s Event | FailedMount | timed out waiting for the condition | 证明挂载尝试耗时过长，直接阻断启动 |
| 3 | K8s Event | FailedMount | hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory | 提供失败的根本原因，确认目录类型或路径错误 |
| 4 | K8s State | Pod Phase | Pending | 确认 Pod 停留在调度完成但未进入运行阶段的初始状态 |
| 5 | Metric | Waiting Reason | kube_pod_container_status_waiting_reason=1 (ContainerCreating) | 独立印证容器一直卡在创建阶段的真实状态 |
| 6 | K8s Config | Resource Limits | CPU: 50m, Memory: 32Mi | 排除资源限制导致容器无法启动的可能（资源上下文） |

证据链表明，Pod 未能从 `Pending` 状态推进到 `ContainerCreating` 以外的阶段。Kubelet 在尝试挂载名为 `input` 的 HostPath 卷时，检测到目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是目录，随后因条件不满足而触发超时。Metrics 的 `waiting_reason` 与 Kubernetes 的 `ContainerCreating` 状态相互验证了该异常持续存在且未被重试消除。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 卷配置指向的路径在 node2 上不存在或并非目录 → Kubelet 执行挂载设置时的类型检查失败 (type check failed) → 挂载操作超时且容器无法启动 → Pod 持续处于 ContainerCreating 状态
```

### 根因结论

已确认的根因为 **HostPath 卷挂载点不匹配**。

输入事实显示，Pod 挂载卷 `input` 时触发了明确的 `FailedMount` 事件（见证据 #3），指出路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是目录。该文件系统的结构错误直接导致 Kubelet 无法完成挂载，进而使容器一直阻塞在 `ContainerCreating` 状态（见证据 #1、#2、#5）。

目前无法确认该路径为何未在 node2 上正确预置（例如：是配置错误、Node 节点故障还是存储卷绑定异常），但当前证据已足以解释“为什么容器无法启动”这一现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.4s
├─ 并发证据采集: 38.6s
│  └─ g1 aiops-case-v06/workload: 38.6s (Evidence 31.1s, RCA 7.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error, pod-imagepull-failed
