## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload stuck in ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: ContainerCreating (fact-182553464325) | 标识异常状态，容器处于初始化阶段 |
| 2 | K8s Event | kubernetes | FailedCreatePodSandBox: failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] (fact-f3c77d079383) | 提供决定性证据，指明 Multus 因找不到 "aiops-unavailable" 插件导致网络创建失败 |
| 3 | K8s Config | kubernetes | k8s.v1.cni.cncf.io/networks: secondary-net (fact-9912cb0cde18) | 关联证据，确认 Pod 配置了 secondary-net 网络，触发了上述 Multus 插件流程 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason=1 (reason=ContainerCreating) (fact-e2e65ae1a677) | 独立维度的同步观测，确认该状态持续存在 |

**证据说明**：
Kubernetes 事件 (事实 2) 直接指出了失败机制：Pod 尝试通过 Multus 插件挂载 `secondary-net` 时，因在 CNI 路径下找不到名为 `aiops-unavailable` 的二进制文件而失败。K8s 状态与 Metric 均证实了这一结果导致容器持续处于 `ContainerCreating` 阶段，无重启现象。

## 🎯 根因分析 · g1

### 因果链

```text
节点 CNI 路径下缺少二进制文件 aiops-unavailable (已验证) → Multus 插件无法添加容器到 secondary-net 网络 (失败机制) → kubelet 触发 FailedCreatePodSandBox 错误 (直接失败) → Pod 卡在 ContainerCreating 状态 (用户可见现象)
```

### 根因结论

根因已确认：**节点 node2 的 CNI 二进制文件路径中缺失了 Multus 二级网络插件所需的 `aiops-unavailable` 二进制文件**。
根据事实 `fact-f3c77d079383`，该缺失文件直接导致 kubelet 无法为 Pod `aiops-case-v14/workload` 创建沙箱环境，引发 `FailedCreatePodSandBox` 错误，使 Pod 永久停滞在 `ContainerCreating` 状态。现有证据充足，无需补充诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.5s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-v14/workload: 36.1s (Evidence 29.6s, RCA 6.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-sandbox-create-failed
