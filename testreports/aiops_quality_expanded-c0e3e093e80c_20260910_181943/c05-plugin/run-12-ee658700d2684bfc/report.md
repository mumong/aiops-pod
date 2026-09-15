## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload 处于 ContainerCreating 状态并卡在 Pending 阶段 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pod aiops-case-v14/workload` 状态 `phase: Pending`，`container.waiting_reason: ContainerCreating` | 确认故障现象为容器创建阶段停滞 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `failed to setup network for sandbox... plugin type="multus" name="multus-cni-network" failed (add)... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接归因：Multus 调用 secondary-net 失败，明确报错为找不到 CNI 插件 `aiops-unavailable` |
| 3 | K8s Config | Kubernetes | 注解 `k8s.v1.cni.cncf.io/networks: secondary-net` 与 `cni.projectcalico.org/podIP:` | 证实 Pod 配置了 Multus 网络引用，解释了为何 kubelet 尝试调用名为 `aiops-unavailable` 的插件 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = `1` | 指标层印证容器处于等待创建网络/沙箱状态 |

**证据说明：**
1. Kubernetes Event (第 2 项) 明确指出了 `kubelet` 执行 CNI 插件 `aiops-unavailable` 时，在 `/opt/cni/bin` 路径下未找到该二进制文件。
2. K8s State (第 1 项) 和 Metric (第 4 项) 从不同维度确认了 Pod 卡在 `ContainerCreating` / `Pending`，与网络配置失败导致的 Sandbox 创建失败现象完全一致。
3. K8s Config (第 3 项) 提供了配置依据，说明 `secondary-net` 网络定义关联了缺失的插件，构成了因果链条的关键证据。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 缺失 CNI 插件 'aiops-unavailable' (事实 #2) → Multus 调用 secondary-net 失败 (事实 #2) → kubelet 无法创建 Pod Sandbox (事实 #1) → Pod 卡在 ContainerCreating (事实 #1)
```

### 根因结论

已确认根因为 **CNI 插件 'aiops-unavailable' 在节点 node2 的 /opt/cni/bin 路径中缺失**。

具体而言：
- **触发原因**：Pod `aiops-case-v14/workload` 配置了 Multus secondary network（注解引用 `secondary-net`）。
- **失败机制**：Kubelet 在创建 Pod Sandbox 时，根据网络配置调用名为 `aiops-unavailable` 的 CNI 插件，但系统报错 `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (事实 #2)。
- **直接结果**：网络设置失败导致 Sandbox 创建失败 (事实 #2)，Pod 无法进入 `Running` 状态，表现为 `ContainerCreating` (事实 #1, #4)。

现有证据已充分支撑该根因，无需日志或追踪数据即可确诊（事实 #3, #4 为辅助确认）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 43.9s
├─ 并发证据采集: 61.5s
│  └─ g1 aiops-case-v14/workload: 61.5s (Evidence 53.6s, RCA 7.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-sandbox-create-failed
