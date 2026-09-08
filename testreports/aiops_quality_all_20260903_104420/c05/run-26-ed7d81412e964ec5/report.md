## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 长期处于 ContainerCreating (Pending) 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (记录 46 条，最近记录 `2m42s`) | 直接证据，明确指出生成错误的 CNI 插件 (multus) 在指定命名空间中找不到指定的网络定义资源。 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: {"container": "app", "reason": "ContainerCreating"} | 确认 Pod 处于调度完成但在容器启动前被阻塞的状态，与 Event 中网络初始化失败的描述一致。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: `1` (labels: `container="app", reason="ContainerCreating"`) | 从监控指标维度量化了 Pod 等待状态的持续存在，与 Kubernetes 事件和状态记录互为印证。 |

**证据说明：**
Kubernetes 事件（#1）提供了最核心的诊断线索，46 条重复的 `NoNetworkFound` 事件确凿地表明 Pod 在启动阶段尝试加载 Multus CNI 插件配置时，因找不到名为 `unavailable-network` 的 `network-attachment-definition` 资源而失败。容器状态（#2）和监控指标（#3）证实了这一失败状态已持续并阻塞了 Pod 的正常运行。尽管 RBAC 限制导致无法直接通过 `kubectl` 列举该 API 资源（`kubectl_find_resource` 和 `kubectl_get_by_kind_in_namespace` 均报 `Forbidden`），但 Multus 插件明确的报错足以证明该配置引用失效。日志与链路追踪不可用，因为 Pod 尚未启动，但这不影响基于 K8s 控制面的判定。

## 🎯 根因分析 · g1

### 因果链

```text
配置错误：Pod 配置引用了不存在的 network-attachment-definition (unavailable-network) → 
Multus CNI 插件尝试获取网络配置失败 (cannot find ... network-attachment-definition) → 
kubelet 报告 FailedCreatePodSandBox (SetupNetwork failed) → 
Pod 长期处于 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的配置中指定了一个名为 `unavailable-network` 的网络附件定义，但在 `aiops-case-05` 命名空间中该资源不存在。

**证据支撑**：
- 46 条 Kubernetes 事件 (`fact-01111675b025` 等) 明确记录 Multus 插件因找不到该资源而报错。
- Pod 状态 (`fact-04ba70c48414`) 和 Prometheus 指标 (`fact-9d21e1ed659e`) 一致显示容器卡在 `ContainerCreating`。

**未知项与局限**：
- 由于权限限制 (RBAC Forbidden)，未能直接列举该 API 资源以 100% 确认其绝对缺失（尽管报错已隐含此结论）。
- 未检查 Node 节点本身的健康状态，但故障机制清晰指向配置引用问题而非节点级网络插件故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 37.3s
├─ 并发证据采集: 56.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 56.2s (Evidence 44.4s, RCA 11.6s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-sandbox-create-failed
