## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh (aiops-case-05) 处于 Pending/ContainerCreating 状态，无法创建 Pod Sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | 持续 1 分钟内反复抛出 `Warning NoNetworkFound`，指出 namespace `aiops-case-05` 中 `network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接定位到 Pod 启动阻塞的具体原因是 CNI 插件无法找到指定的网络附件定义 |
| 2 | K8s State | Kubernetes | 实体 `aiops-case-05/workload-5dbb5dcd6c-bntfh` 状态为 `ContainerCreating` | 确认为启动失败故障，与日志缺失原因一致（容器未启动，仅处于初始化阶段） |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 当前值为 1，未检测到趋势变化 | 提供客观指标印证 Pod 持续卡在等待网络分配的异常状态 |

**证据分析：**
Kubernetes 事件与 Metrics 相互印证，表明该 Pod 处于持续的阻塞状态。根本矛盾点由 `NoNetworkFound` 事件明确指向配置引用缺失，且由于 Pod 处于 `ContainerCreating` 阶段，Pod IP 缺失导致 Tracing 与 Logging 采集不生效（预期现象），故 Kubernetes 事件是判定本次故障的唯一决定性证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置中引用了不存在的网络附件定义 'unavailable-network' (fact-038e6f7c3231) → Multus CNI 报 NoNetworkFound 错误，无法初始化网络接口 → kubelet 持续触发 FailedCreatePodSandBox 警告 (fact-038e6f7c3231) → Pod 停留在 Pending/ContainerCreating 状态，无法创建 Sandbox
```

### 根因结论
**已确认的根因**：Pod 配置中引用了名为 `unavailable-network` 的 CNI NetworkAttachmentDefinition，但该资源在 namespace `aiops-case-05` 中并不存在。
**影响机制**：Multus CNI 在 Pod 初始化阶段因无法找到该网络附件定义而抛出 `NoNetworkFound` 错误，导致网络接口初始化失败。这触发了 kubelet 持续的 `FailedCreatePodSandBox` 重试循环，最终表现为 Pod 始终处于 `ContainerCreating` 状态且无法分配 IP 或进入运行态。依据为 Kubernetes 事件维度（fact-038e6f7c3231）及状态事实（fact-038e6f7c3231）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 32.0s
├─ 并发证据采集: 50.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 50.2s (Evidence 43.5s, RCA 6.5s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed
