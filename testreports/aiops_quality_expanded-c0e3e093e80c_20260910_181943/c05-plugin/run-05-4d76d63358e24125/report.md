## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | 节点 node2 上缺少 CNI 插件二进制文件 'aiops-unavailable'，导致 Multus 无法为 Pod 创建 secondary network 并配置 sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning FailedCreatePodSandBox`: rpc error: failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" failed (add): failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] | 直接定位 Pod 启动失败的机制：CNI 插件文件缺失 |
| 2 | K8s Config | `kubernetes` | Annotation `k8s.v1.cni.cncf.io/networks: secondary-net` | 说明 Pod 尝试挂载 secondary network，触发 Multus 调用 |
| 3 | K8s State | `kubernetes` | Pod 状态 `Pending`，原因 `ContainerCreating` | 确认 Pod 卡在创建阶段，未进入运行状态 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1 (reason=`ContainerCreating`) | 确认 Pod 处于等待状态 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 0 | 排除应用侧崩溃重启或资源耗尽导致的问题 |

上述证据表明：Pod 被调度到节点后，Multus CNI 插件在尝试配置 secondary network (`secondary-net`) 时失败，因为目标节点上找不到名为 `aiops-unavailable` 的 CNI 二进制文件（`failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]`）。这直接导致 Pod 无法创建 sandbox，处于 `Pending/ContainerCreating` 状态，且没有重启计数。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 缺少 CNI 插件文件 'aiops-unavailable' → Multus 无法配置 secondary network → Pod sandbox 创建失败 → Pod 状态卡在 Pending/ContainerCreating
```

### 根因结论

已确认根因：**节点 node2 上缺少 CNI 插件二进制文件 'aiops-unavailable'**。
证据 1 (`fact-9c1b7fbc324d`) 明确显示 `kubelet` 在配置 Multus 插件时无法在系统路径中找到该插件。证据 3 (`fact-e430f5a2904f`) 和 证据 4 (`fact-39fc7cb15103`) 确认了该状态持续存在，且未触发重启。缺失的 CNI 文件导致 Pod 无法完成网络初始化，从而阻塞启动。

---

## 📊 性能统计

```text
├─ 总耗时: 55.9s
├─ 问题定位: 16.5s
├─ 并发证据采集: 30.0s
│  └─ g1 aiops-case-v14/workload: 30.0s (Evidence 23.9s, RCA 6.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
