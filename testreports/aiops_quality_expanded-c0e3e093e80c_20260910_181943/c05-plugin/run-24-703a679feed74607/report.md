## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload (aiops-case-v14) is stuck in ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: rpc error: failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": **failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]** | 直接指出网络插件丢失，导致 Multus 无法配置 `secondary-net`，引发 Pod 沙箱创建失败。 |
| 2 | K8s Config | kubernetes | `k8s.v1.cni.cncf.io/networks: secondary-net` | 确认 Pod 声明了二级网络引用，与事件中的插件调用逻辑一致。 |
| 3 | K8s State | kubernetes | Pod `status`: `Pending` | 确认 Pod 调度失败后的最终状态。 |
| 4 | K8s State | kubernetes | `pod.status` (事实 195ec490ed9) | 验证 Pod 因网络初始化错误卡住，处于 Pending 状态。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}`: `1` | 监控指标证实容器长时间处于等待创建阶段。 |
| 6 | K8s Config | kubernetes | `container.resource_request.cpu`: `5m`, `memory`: `8Mi` | 资源请求极低，排除资源不足导致的节点调度延迟。 |

**证据总结：**
证据 1 (K8s Event) 提供了核心诊断价值，明确指出插件 `aiops-unavailable` 在标准 CNI 路径下不可用，直接导致网络插件失败；证据 2 (K8s Config) 证实了该插件被 Pod 的网络声明引用；证据 3 & 4 (K8s State) 及 5 (Metric) 均验证了 Pod 因网络初始化受阻而处于等待/挂起状态，与根因逻辑闭环。

## 🎯 根因分析 · g1

### 因果链

```text
CNI 插件二进制文件 "aiops-unavailable" 在节点 CNI 路径中缺失 → Multus 尝试为 pod "a2dd4c27..." 配置 "secondary-net" 时找不到所需插件 → Pod 沙箱 (sandbox) 创建失败 (FailedCreatePodSandBox) → Pod 状态永久卡在 ContainerCreating
```

### 根因结论

已确认根因为 **CNI 插件二进制文件 `aiops-unavailable` 在节点上缺失**。Pod 声明了二级网络 `secondary-net`，Multus 插件在创建 Pod 沙箱时尝试加载该插件进行网络配置，但由于节点 `/opt/cni/bin` 路径下找不到该二进制文件，导致网络设置失败，进而阻止了 Pod 的启动。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.6s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-v14/workload: 38.1s (Evidence 30.7s, RCA 7.4s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed
