## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload 处于 ContainerCreating 状态，沙箱创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v14/workload` 状态为 `Pending`，条件 `ContainersReady=False`，原因 `ContainersNotReady` | 确定 Pod 未进入运行状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 处于 `waiting` 状态，原因 `ContainerCreating` | 明确故障发生在容器运行时环境创建阶段 |
| 3 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `failed to setup network for sandbox`: plugin type="multus" name="multus-cni-network" failed: failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接证明沙箱创建失败及具体缺失的组件 |
| 4 | K8s Config | Kubernetes | Pod 配置 `k8s.v1.cni.cncf.io/networks: secondary-net` | 确认 Pod 依赖次级网络 CNI 插件 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 1 | 独立证实容器卡在等待创建阶段的指标事实 |

**证据说明：**
Kubernetes 事件（#3）与状态（#2）一致指向沙箱创建失败，根本原因是 CNI 插件缺失。指标事实（#5）独立印证了容器处于 `ContainerCreating` 的挂起状态，排除了偶发性网络抖动，确认为配置或环境层面的硬性缺失。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 /opt/cni/bin 缺少 'aiops-unavailable' 插件二进制文件 → Multus 调用次级网络插件失败 → kubelet 无法创建 Pod 沙箱 → Pod 陷入 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因：** Pod `aiops-case-v14/workload` 的 CNI 插件配置错误或缺失。

Pod 配置了依赖 `multus` 和次级网络 `secondary-net` 的网络设置，该网络要求使用名为 `aiops-unavailable` 的 CNI 插件。然而，目标节点 `node2` 的 CNI 路径 `/opt/cni/bin` 下不存在该插件的二进制文件，导致 `kubelet` 在执行沙箱创建时抛出 `failed to find plugin` 错误，致使容器无法创建。

*证据支撑：*
- CNI 插件缺失及报错原文见事实 #3 (`FailedCreatePodSandBox`)。
- Pod 挂载次级网络见事实 #4 (`secondary-net` 配置)。
- 容器处于创建等待状态见事实 #2 与 #5 (`ContainerCreating`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 41.6s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-v14/workload: 40.3s (Evidence 32.3s, RCA 7.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
