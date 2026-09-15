## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 中定义的 HostPath 卷 'input' 指向宿主机路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 不存在或类型不符（非目录），导致 kubelet 挂载失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod phase: `Pending`, status: `Pending` (fact-6fe15cb643d3) | 确定 Pod 处于调度后但未运行的停滞状态 |
| 2 | K8s Event | Kubernetes | `FailedMount`: hostPath type check failed: `/var/lib/aiops-fixture-unavailable-7f394bef/input` is not a directory (fact-de260a16da5c) | 直接指明挂载失败的原因为宿主机路径检查不通过 |
| 3 | K8s State | Kubernetes | Pod condition: `ContainersReady=False` (ContainersNotReady), `Ready=False` (ContainersNotReady) (fact-3ae226773f63, fact-c4693a3b3572) | 确认容器因资源准备不足未就绪，与事件原因吻合 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 (fact-b988d5c23321) | 验证容器卡在创建等待期，未进入运行态 |

K8s Event 直接记录了具体的挂载错误信息，而 Metric 确认了该错误导致的持续等待状态，两者共同锁定了问题范围。由于 Pod 未启动，无日志或 Tracing 数据。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 不存在或类型不符 (非目录) → kubelet 挂载 HostPath 卷失败 (FailedMount) → 容器保持 ContainerCreating 状态 → Pod 状态为 Pending 且不可用
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v06/workload` 中定义的 `HostPath` 卷 `input` 指向宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不存在或类型不符（非目录），导致 kubelet 挂载失败。

证据编号 [1] 和 [3] 显示 Pod 卡在挂载阶段，证据编号 [2] 明确指出错误原因为 `hostPath type check failed`，且证据编号 [4] 证实容器处于 `ContainerCreating` 等待状态。现有 K8s 事实已充分支撑此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 58.7s
├─ 问题定位: 22.2s
├─ 并发证据采集: 28.1s
│  └─ g1 aiops-case-v06/workload: 28.1s (Evidence 22.6s, RCA 5.4s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
