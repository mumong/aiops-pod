## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload (aiops-case-v14) stuck in ContainerCreating/Pending status; kubelet FailedCreatePodSandBox due to network setup failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] (fact-08db31b74e1c) | 直接证据：Kubelet 无法定位 CNI 插件导致沙箱创建失败 |
| 2 | K8s Config | kubernetes | Pod 注解 `k8s.v1.cni.cncf.io/networks: secondary-net` (fact-19c5c2f39e6b) | 关联证据：确认 Pod 配置了 Multus 二级网络并引用了上述网络配置 |
| 3 | K8s Config | kubernetes | 资源限制：CPU 50m / 内存 32Mi (fact-0b7e04f81685, fact-2d5f4de57925) | 排除资源过载导致调度/启动失败，确认问题在网络初始化阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 `1` (reason=ContainerCreating) (fact-7e20315d0422) | 症状确认：Pod 处于 ContainerCreating 等待状态，符合网络插件缺失导致的停滞特征 |

**证据印证说明：**
Kubernetes 事件明确指出缺少 `aiops-unavailable` 插件，与 Pod 配置中的 `secondary-net` Multus 网络注解（fact-2）形成闭环。Metric 数据（fact-4）进一步验证了 Pod 因 CNI 配置失败而长期处于 ContainerCreating 状态的停滞现象，且未发生重启。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了引用缺失插件的 Multus 网络 → Kubelet 在 node2 初始化沙箱时无法找到插件 → 抛出 FailedCreatePodSandBox 错误 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因：** 调度节点 (node2) 的 CNI 插件路径 (`/opt/cni/bin`) 中缺失名为 `aiops-unavailable` 的二进制文件。由于 Pod (aiops-case-v14/workload) 配置了使用此插件的 Multus 二级网络 (`secondary-net`)，Kubelet 在创建 Pod 沙箱阶段因无法初始化网络而直接失败，导致 Pod 无法启动并进入 Pending 状态。

支撑证据：
- 事件 `FailedCreatePodSandBox` 明确指出未找到插件 (事实 #1)。
- Pod 网络配置指向了 `secondary-net` (事实 #2)。
- 资源限制极低 (事实 #3) 排除了资源瓶颈。
- 监控指标确认 Pod 卡在等待状态 (事实 #4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.3s
├─ 并发证据采集: 50.8s
│  └─ g1 aiops-case-v14/workload: 50.8s (Evidence 40.9s, RCA 9.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed
