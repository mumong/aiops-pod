## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 处于 Pending/ContainerCreating 状态，Sandbox 创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed ... error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin ...]` (fact-fad2719c3a6d) | 致命证据：Kubelet 报告 Multus 插件在节点路径中找不到 `aiops-unavailable`，直接导致 Pod 沙箱创建失败 |
| 2 | K8s State | Pod Status | `status: Pending` (fact-edc644aec686) | 症状：Pod 因网络配置错误停留在创建阶段，未进入 Running 或 Error 状态 |
| 3 | K8s Event | Kubelet | `Warning  FailedCreatePodSandBox  22m` (fact-fad2719c3a6d) | 症状：该失败状态已持续 22 分钟，表明重试机制未能恢复 |
| 4 | K8s Config | Annotations | `cni.projectcalico.org/networks: secondary-net` (fact-aad8318a9521) | 背景：Pod 被配置了名为 `secondary-net` 的附属网络，这正是触发 Multus 调用 `aiops-unavailable` 插件的原因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating) = 1 (fact-236474ffc8bb) | 佐证：确认 Pod 容器处于等待网络或拉取状态，与 CNI 失败现象一致 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (phase=Failed) = 0 (fact-172a4548ad5a) | 排除：Pod 整体尚未被判定为 Failed 阶段，符合 CNI 阻塞在初始沙箱创建的阶段特征 |

证据表明，Pod 的 `secondary-net` 配置要求 Multus 加载一个名为 `aiops-unavailable` 的插件，但调度到 `node2` 的节点路径中并不存在该插件。Metric 确认了等待状态，且排除了更广泛的 Pod 崩溃。Kubelet 的报错直接指明了缺失的组件是网络插件。

## 🎯 根因分析 · g1

```text
Pod 配置引用了不存在的 CNI 插件 aiops-unavailable → Multus 在节点 node2 路径 /opt/cni/bin 中找不到该插件 → 网络初始化失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v14/workload` 的网络配置（`secondary-net`）引用了一个名为 `aiops-unavailable` 的插件，但在该 Pod 调度的节点（node2）的 CNI 二进制路径 `/opt/cni/bin` 中，该插件文件不存在。

**证据引用**：
- 直接事实支撑见证据 #1 (fact-fad2719c3a6d)，Kubelet 明确报出 `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin ...]`。
- 配置关联见证据 #4 (fact-aad8318a9521)，证实了 `secondary-net` 配置的存在。
- 现象一致性见证据 #2 (fact-edc644aec686) 和 #5 (fact-236474ffc8bb)，Pod 状态和 Metric 均反映为创建阶段挂起。

**结论**：故障根因是网络插件缺失或路径配置错误，导致容器无法分配网络。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.1s
├─ 并发证据采集: 31.3s
│  └─ g1 aiops-case-v14/workload: 31.3s (Evidence 22.2s, RCA 9.0s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
