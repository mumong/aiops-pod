## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating / Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 证实 Pod 处于无法进入就绪的停滞状态 |
| 2 | K8s Event | kubernetes | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 暴露核心缺失资源，持续报错频率达 46 次，直接说明 CNI 依赖不存在 |
| 3 | K8s Event | kubernetes | `FailedCreatePodSandBox`: `failed to setup network for sandbox... plugin type="multus" name="multus-cni-network" failed` | 描述底层失败机制，Multus 插件因查找失败导致容器沙箱无法创建 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating): `1` | 确认 Pod 持续处于等待阶段，无状态切换 |
| 5 | Logging | elasticsearch | `not_applicable` | 因 Pod 卡在启动前，无物理日志产出，印证故障处于调度与网络层 |
| 6 | Tracing | deepflow, tempo | `not_applicable` | `pod_ip is empty`，无网络通信记录，排除业务层问题 |

**证据综述：**
多源事实高度一致。Kubernetes 事件 (E2, E3) 给出了明确的失败链条（找不到定义 → Multus 失败 → 沙箱创建失败），Pod 状态 (E1) 和指标 (E4) 验证了该现象的持续性。由于无法获取应用日志与追踪，故障隔离在基础设施配置层，即 Pod 引用的网络配置项缺失。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件因找不到定义而加载失败 → kubelet 无法创建容器沙箱 (CNI 失败) → Pod 卡死在 ContainerCreating / Pending 状态
```

### 根因结论

已确认根因为 **网络配置依赖缺失**：Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 被配置请求加入名为 `unavailable-network` 的网络（证据 #2, #3），但 K8s 集群中该 `NetworkAttachmentDefinition` 资源不存在。这一配置错误导致 Multus CNI 插件在尝试配置网络时直接失败，进而阻断了容器沙箱的创建。

**未知信息：**
无法确认 `unavailable-network` 是预期存在的资源被遗漏，还是 Pod 注解本身存在拼写错误/配置失误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 34.2s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 43.9s (Evidence 33.6s, RCA 10.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed
