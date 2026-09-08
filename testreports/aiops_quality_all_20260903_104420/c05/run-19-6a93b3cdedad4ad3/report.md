## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 处于 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `NoNetworkFound`：cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) [fact-04e5419793ca, 46 records] | 证明 Pod 请求的网络定义缺失，是调度停滞的直接原因 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox`：Multus plugin failed to setup network for sandbox due to not found "unavailable-network" [fact-1f3e1142ce2c, 176x aggregate] | 确认 Kubelet 因网络插件失败而持续重试创建 Sandbox |
| 3 | K8s State | kubernetes | `ContainerCreating`：container "app" 状态处于等待原因 "ContainerCreating" [fact-fd9f1d6f1907] | 证实 Pod 卡在启动阶段，容器未进入就绪状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1，labels: reason="ContainerCreating" [fact-cf763a036202] | 独立于事件日志，确认 Pod 长期处于 Waiting 状态 |

**证据说明：**
- K8s 事件与状态直接印证：Pod 卡死在 `ContainerCreating` [3]，原因是 Kubelet 的 `FailedCreatePodSandBox` [2]。
- 错误根因一致：Kubelet 的失败原因与 Multus 插件的 `NoNetworkFound` [1] 完全一致，均指向找不到 `unavailable-network` 定义。
- Metric [4] 作为独立数据源，确认了该异常状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 注解引用 'unavailable-network' → Multus 插件在 aiops-case-05 命名空间查找不到该 NAD → CNI Setup 失败触发 FailedCreatePodSandBox → Pod 卡死在 ContainerCreating
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 配置了不存在的 Multus NetworkAttachmentDefinition `unavailable-network`。Multus CNI 插件在初始化网络时无法找到该资源（证据 1），导致 Kubelet 无法创建 Pod Sandbox（证据 2），从而使 Pod 停滞在 `ContainerCreating` 状态（证据 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 11.2s
├─ 并发证据采集: 56.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 56.4s (Evidence 46.5s, RCA 9.7s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- 未调用 Runbook
