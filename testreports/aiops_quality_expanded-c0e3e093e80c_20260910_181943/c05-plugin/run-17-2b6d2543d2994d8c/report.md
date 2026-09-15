## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload 持续处于 ContainerCreating/Pending 状态，未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: Failed to create pod sandbox: rpc error... failed to setup network... plugin type="multus" name="multus-cni-network" failed... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] | 核心归因：明确报错插件丢失，导致沙箱创建失败 |
| 2 | K8s Config | Kubernetes | `k8s.v1.cni.cncf.io/networks: secondary-net` | 确认 Pod 引用了 Multus 附加网络 |
| 3 | K8s State | Kubernetes | Pod `workload` 处于 `Pending` 状态 | 验证故障现象与事件时间戳（21m前）一致 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `ContainerCreating`) | 监控视角确认容器处于等待状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认 Pod 尚未成功启动过，排除重启循环 |

**证据关系说明：**
Kubernetes 事件 (fact-12c624ae6d8f) 直接指出了根本原因，即网络插件 `aiops-unavailable` 缺失。K8s 配置 (fact-b09dd3d5d8ca) 证实了 Pod 确实尝试使用了该 Multus 网络。Metric 数据 (fact-845080b818bf, fact-1293e7d01333) 从监控维度佐证了 Pod 停滞在启动阶段且无运行记录。由于容器未启动，Logging 和 Tracing 数据缺失符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的 CNI 插件 aiops-unavailable → kubelet 加载插件失败并报错 → 网络初始化终止，Pod 沙箱创建失败 → Pod 持续处于 Pending / ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v14/workload` 配置了 Multus 附加网络 `secondary-net`，该网络引用了名为 `aiops-unavailable` 的 CNI 插件，但该插件在调度节点的 `/opt/cni/bin` 路径下缺失。这导致 `kubelet` 在创建 Pod 沙箱时因插件初始化失败而终止流程（证据 #1, #2）。

**佐证**：
- **状态验证**：Pod 处于 `Pending` 状态且重启次数为 0，说明从未进入可运行阶段，符合启动失败的逻辑（证据 #3, #5）。
- **监控确认**：Prometheus 指标显示 `ContainerCreating` 等待原因持续存在（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 32.6s
├─ 并发证据采集: 69.2s
│  └─ g1 aiops-case-v14/workload: 69.2s (Evidence 62.4s, RCA 6.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error
