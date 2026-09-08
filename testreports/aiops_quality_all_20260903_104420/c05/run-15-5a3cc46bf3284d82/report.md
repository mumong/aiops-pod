## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-0150dc979a65, fact-058bae1e984e, fact-338f653bb6c7 等) | 确认 Namespace `aiops-case-05` 下缺少名为 `unavailable-network` 的网络插件配置，持续存在约 47 分钟 |
| 2 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox ... kubelet: ... plugin type="multus" name="multus-cni-network" failed (add): ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-2c874bd34510, fact-3a8774757029, fact-500fa5099ac2) | 确认 `kubelet` 因 Multus CNI 无法获取网络委托配置，进而导致 Pod 沙箱创建失败 |
| 3 | K8s State | kubernetes | `container.waiting_reason: {"container": "app", "reason": "ContainerCreating"}` (fact-f2cd5bae06ca) | 证实应用容器 `app` 停留在 `ContainerCreating` 状态，处于等待网络初始化阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，`labels: container="app", reason="ContainerCreating"`, `sample_count=1` (fact-cdf00622c6db) | 从监控视角确认 Pod 当前处于 `ContainerCreating` 等待原因，与 K8s 状态一致 |

**证据关联说明：**
Kubernetes 事件明确指出了 `multus` 插件因找不到 `unavailable-network` 网络附加定义而失败，直接导致 `kubelet` 报出 `FailedCreatePodSandBox` 错误；这种网络配置的缺失直接解释了为何应用容器会无限期停留在 `ContainerCreating` 状态，且 Metric 数据实时佐证了这一状态的存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 NetworkAttachmentDefinition -> Multus CNI 插件无法获取网络委托配置 -> Pod 沙箱（网络部分）创建失败 -> 容器卡在 ContainerCreating 状态
```

### 根因结论

根因确认：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的配置要求挂载一个名为 `unavailable-network` 的网络附加定义（NetworkAttachmentDefinition），但 `aiops-case-05` 命名空间中实际上并不存在该资源。这导致 Multus CNI 插件在初始化网络时因找不到对应委托而失败，进而阻断了 `kubelet` 对 Pod 沙箱的创建过程，使容器持续处于 `ContainerCreating` 状态。主要证据来源于 Kubernetes 事件（fact-1, fact-2）和状态（fact-3）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 17.3s
├─ 并发证据采集: 560.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 560.1s (Evidence 550.9s, RCA 9.0s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
