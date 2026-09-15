## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | aiops-case-v14/workload pod stuck in ContainerCreating/Pending state due to network setup failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: `failed to setup network for sandbox "a2dd4c27...": plugin type="multus" ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 明确根因：多租户插件二进制文件丢失导致沙箱创建失败 |
| 2 | K8s Config | kubernetes | `k8s.v1.cni.cncf.io/networks: secondary-net` | 提供触发上下文：Pod 尝试挂载名为 `secondary-net` 的网络 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason[reason="ContainerCreating"]` = `1` | 确认容器状态停留在创建前阶段，与 CNI 插件失败现象一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` | 排除因应用层异常导致重启的可能性 |
| 5 | K8s State | kubernetes | `pod.status`: `Pending` | 确认 Pod 因网络依赖未满足而无法进入运行态 |

**证据印证说明：**
- **K8s Event (fact-f52f6611194e)** 给出了确切的失败原因：`aiops-unavailable` 插件缺失。这与 **K8s Config (fact-54e7aeab1c25)** 中定义的 `secondary-net` 网络配置直接关联。
- **Metric (fact-b3c143a0180a, fact-a49431b3bf2b)** 确认了 Pod 处于 `ContainerCreating` 等待状态且重启数为 0，从侧面证实了故障发生在启动初期，而非应用运行时。
- **Logging/Tracing** 因 Pod 无法启动且无 Pod IP 被判定为不可用，缺乏数据支持，但这符合预期的故障传播路径（CNI 失败 -> Pod Pending -> 无日志/Trace）。

## 🎯 根因分析 · g1

### 因果链

```text
CNI 插件二进制文件 'aiops-unavailable' 从节点路径缺失 → Multus 在挂载 secondary-net 时无法加载指定插件导致网络初始化失败 → kubelet 创建 Pod 沙箱（FailedCreatePodSandBox） → Pod 卡在 ContainerCreating 状态，无法启动应用
```

### 根因结论

**已确认的根因：**
集群节点 `/opt/cni/bin` 路径下缺失由 `aiops-unavailable` 插件所需的 CNI 二进制文件（引用 **证据 #1**）。由于 Pod `aiops-case-v14/workload` 配置了依赖 Multus 和该插件的 `secondary-net` 网络（引用 **证据 #2**），导致 `kubelet` 在创建 Pod 沙箱时网络设置步骤失败。这直接导致了 Pod 持续处于 `Pending/ContainerCreating` 状态（引用 **证据 #5**），且 `ContainerCreating` 等待指标为 1（引用 **证据 #3**）。

**未确认事项：**
- 导致 `aiops-unavailable` 插件缺失的具体系统原因（例如：安装脚本未执行、DaemonSet 故障或文件被误删）。
- `NetworkAttachmentDefinition` 中引用的插件名称是否准确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.6s
├─ 并发证据采集: 34.7s
│  └─ g1 aiops-case-v14/workload: 34.7s (Evidence 25.6s, RCA 9.0s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed
