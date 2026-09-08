## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 卡在 ContainerCreating (Pending) 状态，无法创建沙箱 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox: Failed to create pod sandbox: rpc error: ... failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add)` | 证实 Pod 在创建阶段因网络插件失败而受阻，处于卡死状态 |
| 2 | K8s Event | multus | `NoNetworkFound: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 精准定位网络失败的具体原因：Multus 找不到名为 `unavailable-network` 的 CNI 定义 |
| 3 | K8s Config | Pod Annotations | `k8s.v1.cni.cncf.io/networks: unavailable-network` | 暴露 Pod 的显式引用配置，与事件中的缺失对象直接对应 |
| 4 | K8s State | Pod/Container | `Status: ContainerCreating` / `Ready: False (ContainersNotReady)` | 描述当前 Pod 的最终停滞状态，证实启动未成功 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 从监控维度确认该 Pod 处于等待状态，且非 `Failed` 或 `OOMKilled` 等应用/资源型原因 |

**证据关联说明：**
事件 (fact-1, fact-2) 给出了明确的错误堆栈，指出 Multus 插件报错是因为找不到 `unavailable-network` 定义；配置 (fact-3) 在 Pod 的 Annotations 中找到了该引用的确切位置，形成了从“定义缺失”到“插件报错”再到“Pod 卡住”的完整事实闭环。指标 (fact-5) 排除了其他等待原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 声明了不存在的 network-attachment-definition 'unavailable-network' → Multus CNI 插件查找失败并返回 'not found' 错误 → Kubelet 因网络设置失败无法创建 Pod Sandbox → Pod 状态维持在 ContainerCreating/Pending，无业务日志或 Trace 产生
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的配置中存在对 NetworkAttachmentDefinition `unavailable-network` 的引用（证据编号 3），但该定义在 `aiops-case-05` 命名空间中不存在（证据编号 2）。这导致 Multus CNI 插件无法完成网络配置，进而导致 Kubelet 创建沙箱失败（证据编号 1），最终 Pod 卡在 `ContainerCreating` 状态（证据编号 4）。

由于容器未能成功启动，未产生任何应用日志或业务流量（Logging/Tracing 维度缺失为物理预期，非故障掩盖）。现有 Kubernetes 事件与配置事实已构成充分证据，足以解释当前故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.3s
├─ 并发证据采集: 44.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 44.4s (Evidence 36.5s, RCA 7.7s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
