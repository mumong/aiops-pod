## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload (aiops-case-v14) 处于 ContainerCreating/Pending 状态，Kubelet 报错 FailedCreatePodSandBox，导致容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (fact-ce7ab0ed24f7) | 直接证据：明确指出了缺失的二进制文件路径与具体组件名称。 |
| 2 | K8s State | kubernetes | Pod `aiops-case-v14/workload` 处于 `Pending` 状态 (fact-711afd587f13) | 现象确认：与 Sandbox 创建失败导致的启动挂起一致。 |
| 3 | K8s Config | kubernetes | Pod 配置 `k8s.v1.cni.cncf.io/networks: secondary-net` 引用外部网络插件 (fact-21bf7efe4eca) | 因果背景：解释了为何 kubelet 需要寻找特定插件而非默认插件。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `ContainerCreating`) (fact-748a67fcd867) | 支持证据：确认容器处于因网络/启动阻塞导致的等待状态，重启计数为 0。 |

证据 1 (Event) 指出在 `/opt/cni/bin` 路径下找不到 `aiops-unavailable` 插件。证据 3 (Config) 确认了该 Pod 的 `secondary-net` 配置明确要求调用此非标准插件。由于插件文件缺失（证据 1），Kubelet 无法完成网络配置，导致 Pod 无法进入 Running 状态（证据 2）。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 的 CNI 路径 (/opt/cni/bin) 中缺失插件二进制文件 'aiops-unavailable' (证据1)
  →
Pod (aiops-case-v14/workload) 的网络配置引用了该特定插件 (证据3)
  →
Kubelet 执行网络初始化失败，触发 FailedCreatePodSandBox 错误 (证据1)
  →
Pod 处于 Pending/ContainerCreating 状态无法启动 (证据2, 证据4)
```

### 根因结论

**已确认根因**：Pod `aiops-case-v14/workload` 因依赖的 CNI 插件 `aiops-unavailable` 在节点 `node2` 上文件缺失，导致网络初始化失败。

*   **依据**：Kubernetes Event `fact-ce7ab0ed24f7` 提供了明确的错误描述，指出路径下缺少该插件。Pod 配置 `fact-21bf7efe4eca` 证实了其对特定插件的强依赖。Metric `fact-748a67fcd867` 佐证了 Pod 因等待网络配置而处于阻塞状态。
*   **未知项**：CNI 插件 `aiops-unavailable` 的预期部署来源（如特定的 DaemonSet）及其在当前节点上丢失的具体原因（是未部署还是部署失败）在现有事实中尚未查明，但这不改变“插件缺失导致当前启动失败”的直接根因。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 20.6s
├─ 并发证据采集: 28.3s
│  └─ g1 aiops-case-v14/workload: 28.3s (Evidence 20.8s, RCA 7.3s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-sandbox-create-failed
