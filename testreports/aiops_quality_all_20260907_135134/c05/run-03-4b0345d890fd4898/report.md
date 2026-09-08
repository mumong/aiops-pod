## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx (ns: aiops-case-05) stuck in ContainerCreating/Pending status |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` [fact-05016bb7cf20] | 直接指出 Multus CNI 无法找到指定的网络配置资源 |
| 2 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox ... plugin type="multus" name="multus-cni-network" failed (add): ... getKubernetesDelegate: cannot find a network-attachment-definition ... not found` [fact-1b4d2c103a22] | 确认沙箱创建失败的根本机制是 CNI 插件调用失败 |
| 3 | K8s Config | kubernetes | `Annotations: k8s.v1.cni.cncf.io/networks: unavailable-network` [fact-fd9b6413e34a] | 确认 Pod 配置显式请求了一个名为 `unavailable-network` 的 CNI 网络 |
| 4 | K8s State | kubernetes | `pod.status: Pending` [fact-6d6d3398e612] / `container.waiting_reason: ContainerCreating` [fact-73529a473b9e] | 确认异常表现状态为持续等待，未进入运行阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` [fact-a5a81e6648a4] | 外部指标观测证实容器确实处于等待状态 |

**证据说明：**
Kubernetes 事件 [fact-05016bb7cf20, fact-1b4d2c103a22] 一致表明 Multus 插件因找不到 `unavailable-network` 资源而失败；Pod 注解 [fact-fd9b6413e34a] 证明了该资源的配置来源；指标 [fact-a5a81e6648a4] 与 Pod 状态 [fact-73529a473b9e] 互相印证了这一等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
Missing NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 解析失败 → 无法创建 Pod Sandbox → 容器状态卡死在 ContainerCreating
```

### 根因结论

已确认根因为命名空间 `aiops-case-05` 中不存在 CNI 网络定义资源 `unavailable-network`（引用证据：[fact-05016bb7cf20]）。Pod 配置显式请求了该网络（引用证据：[fact-fd9b6413e34a]），导致 Multus 插件在初始化时查找失败（引用证据：[fact-1b4d2c103a22]），进而阻止了容器沙箱的创建（引用证据：[fact-6d6d3398e612]）。现有证据确凿，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 25.3s
├─ 并发证据采集: 54.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 54.8s (Evidence 47.0s, RCA 7.7s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
