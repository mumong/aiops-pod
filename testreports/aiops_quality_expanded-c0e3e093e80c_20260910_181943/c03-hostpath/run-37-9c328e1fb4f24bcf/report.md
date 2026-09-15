## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 在节点 node2 上调度，但 Volume 'input' 挂载失败。根本原因是宿主机的 HostPath 路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不存在或非目录，导致 kubelet 无法完成 VolumeSetUp，Pod 卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | fact-aa9de2b1b28a | `Warning FailedMount` ... `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接指明挂载失败的具体原因：宿主机路径不存在或非目录 |
| 2 | K8s Event | fact-5d0ac5ce8f07 | `Warning FailedMount` ... `timed out waiting for the condition` (持续68m) | 证明故障处于持续挂起状态，而非偶发瞬时错误 |
| 3 | Metric | fact-6745980881f5 | `kube_pod_container_status_waiting_reason` = 1 (reason=ContainerCreating) | 确认 Pod 长期停留在容器创建等待阶段，未进入运行态 |
| 4 | Metric | fact-f5842427286a | `kube_pod_container_status_restarts_total` = 0 (container=app) | 确认容器尚未成功启动过，排除了因容器启动后崩溃导致的重启可能 |

Kubernetes 事件（#1, #2）与 Metrics（#3）高度一致，共同指向了 Pod 因底层存储挂载失败而卡在 `ContainerCreating` 阶段的单一事实链条。

## 🎯 根因分析 · g1

### 因果链

```text
宿主路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 无效 → kubelet 执行 VolumeSetUp 类型检查失败 → Pod 挂载卷超时挂起 → 现象：Pod 状态卡在 ContainerCreating
```

### 根因结论

已确认根因为 **Pod 挂载卷失败导致调度挂起**。
具体证据支持如下：
1. **直接原因**：Kubernetes Event `fact-aa9de2b1b28a` 明确指出 `hostPath type check failed`，说明 Pod 定义中引用的 HostPath `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度节点上并非有效目录。
2. **当前状态**：Metrics `fact-6745980881f5` 和 Event `fact-5d0ac5ce8f07` 证实该挂载失败状态已持续近 1 小时，Pod 无法进入 `Running` 状态。
3. **排除其他因素**：Metrics `fact-f5842427286a` 显示重启次数为 0，排除了应用逻辑错误或资源争抢导致的启动失败。

---

## 📊 性能统计

```text
├─ 总耗时: 51.1s
├─ 问题定位: 15.2s
├─ 并发证据采集: 27.0s
│  └─ g1 aiops-case-v06/workload: 27.0s (Evidence 19.3s, RCA 7.6s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error, pod-sandbox-create-failed
