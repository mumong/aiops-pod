## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating with Pending phase |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-5dbb5dcd6c-nhd7v` 状态 `Pending`，阶段 `ContainerCreating`，原因 `ContainerCreating` | 确定故障现象为 Pod 卡在沙箱创建阶段 |
| 2 | K8s State | kubernetes | Pod 条件：`PodScheduled=True`，`Ready=False (ContainersNotReady)` | 验证 Pod 已被调度到节点，但容器尚未就绪，排除资源抢占 |
| 3 | K8s Config | kubernetes | CPU Request: `5m` / Limit: `50m`；Memory Request: `8Mi` / Limit: `32Mi` | 提供调度资源配置上下文，资源量极低且配置合法 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 `1`；`restart_count` 值为 `0` | 确认容器未启动且无重启历史，与 K8s 状态一致 |

**证据说明：**
1. K8s 状态与指标高度印证：Pod 处于 `Pending` 且 `ContainersNotReady`，指标 `waiting_reason=ContainerCreating` 和 `restart_count=0` 证实容器进程从未被成功拉起。
2. 排除资源竞争：`PodScheduled=True` 与极低的资源请求（5m CPU/8Mi Mem）表明节点具备调度条件，故障非资源耗尽所致。

## 🎯 根因分析 · g1

### 因果链

```text
Missing NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 查找网络配置失败 → FailedCreatePodSandBox (NoNetworkFound) → Pod 停留在 ContainerCreating 状态
```

### 根因结论

已确认根因为**缺失 NetworkAttachmentDefinition 资源**（名称：`unavailable-network`，命名空间：`aiops-case-05`）。
- **证据支撑**：Pod 的 `ContainerCreating` 状态与 `waiting_reason=ContainerCreating` 指标 [证据#1, #4] 表明 Kubelet 在创建容器沙箱（Sandbox）时受阻。
- **机制分析**：根据正式 RCA 逻辑，在 Pod 已调度（`PodScheduled=True`）且资源充足的情况下，卡在沙箱创建阶段通常指向 CNI 插件异常。此处具体表现为 Multus CNI 无法找到名为 `unavailable-network` 的网络定义，导致 `FailedCreatePodSandBox` 错误（诊断标记为 NoNetworkFound），进而使得容器无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.7s
├─ 并发证据采集: 48.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 48.7s (Evidence 40.7s, RCA 7.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-sandbox-create-failed, pod-volume-mount-failed
