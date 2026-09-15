## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload stuck in ContainerCreating state due to FailedCreatePodSandBox |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox`: failed to setup network for sandbox "...79c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] | 明确定位故障原因为 CNI 插件缺失，导致 Pod 沙箱创建失败。 |
| 2 | K8s Event | kubernetes | `Annotations: cni.projectcalico.org/containerID: a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7`<br>`k8s.v1.cni.cncf.io/networks: secondary-net` | 证实 Pod 声明了 `secondary-net` 网络依赖，是触发 Multus 调用的配置上下文。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-aeb9aa4e59b5) | 验证 Pod 处于等待网络或容器配置完成的阻塞状态。 |
| 4 | K8s State | kubernetes | `pod.status`: Pending (fact-790a70e3c631) | 确认 Pod 处于 Pending 阶段，尚未调度到运行状态，与事件中的沙箱创建失败逻辑一致。 |

**证据综合：**
Kubernetes 事件日志 (证据 1) 直接指认出 `aiops-unavailable` 插件在节点 `/opt/cni/bin` 路径下缺失，这是导致 `FailedCreatePodSandBox` 的直接原因。该原因解释了为何带有 `secondary-net` 网络声明的 Pod (证据 2) 无法初始化，从而表现为 `ContainerCreating` 的等待状态 (证据 3) 和 `Pending` 阶段状态 (证据 4)。

## 🎯 根因分析 · g1

### 因果链

```text
节点缺失 CNI 插件 "aiops-unavailable" → Multus 无法解析并加载插件完成 secondary-net 配置 → FailedCreatePodSandBox (kubelet 事件) → Pod 阻塞在 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因为：**节点 `/opt/cni/bin` 目录下缺少 CNI 插件二进制文件 `aiops-unavailable`**。

证据 (事实 ID: fact-067e879ad9a7) 中的 K8s 事件日志明确记录，在尝试为 Pod 创建沙箱并配置网络时，Multus CNI 插件无法在指定路径中找到该二进制文件，导致网络配置失败。这一底层错误直接阻断了 Pod 的生命周期，导致用户观察到 Pod 无法运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.6s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v14/workload: 35.7s (Evidence 29.1s, RCA 6.6s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
