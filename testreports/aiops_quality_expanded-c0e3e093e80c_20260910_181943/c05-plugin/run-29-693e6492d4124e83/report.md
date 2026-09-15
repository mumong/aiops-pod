## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload in namespace aiops-case-v14 is stuck in ContainerCreating/Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Pending; `pod.phase`: Pending; `container.waiting_reason`: ContainerCreating | 描述 Pod 卡在调度后、容器启动前的状态，与网络配置阶段阻塞一致。 |
| 2 | K8s Event | Kubernetes | `event.message`: "Warning FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type=\"multus\" ... error adding container to network \"secondary-net\": failed to find plugin \"aiops-unavailable\" in path [/opt/cni/bin /opt/cni/bin]" | 直接证实 CNI 插件缺失是引发网络初始化失败的根本错误。 |
| 3 | K8s Event | Kubernetes | 聚合 Event 信息: `k8s.v1.cni.cncf.io/networks: secondary-net`, `Annotations: cni.projectcalico.org/containerID: ...` | 证实 Pod 配置了 Multus 调用 secondary-net 网络，该网络请求了缺少的插件。 |
| 4 | K8s Config | Kubernetes | 容器资源请求/限制: `memory: 8Mi/32Mi`, `cpu: 5m/50m` | 排除内存不足作为 Pod 无法调度的可能原因。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` | 确认容器当前仍处于等待创建状态，无重启记录(`kube_pod_container_status_restarts_total = 0`)。 |

**证据分析：**
Kubernetes 状态与事件提供了完整的故障链条：Pod 被调度为 Pending 且处于 ContainerCreating 等待态，对应 Event 明确报出 CNI 插件缺失错误。Metric 数据从时序指标角度确认了这一停滞状态且未发生重启。由于容器未启动，Logging 与 Tracing 维度为空。证据与官方 RCA 完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
节点上缺失 CNI 二进制插件 'aiops-unavailable' → Multus CNI 无法为 secondary-net 网络初始化网络环境 → kubelet 返回 FailedCreatePodSandBox 错误 → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因：**
Pod 调度失败的根本原因是 Multus CNI 插件在节点上缺少必要的二进制文件 'aiops-unavailable'（证据：[#2] K8s Event 明确报错 `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]`）。这导致 `FailedCreatePodSandBox` 错误，进而使 Pod 停留在 `ContainerCreating` 状态（证据：[#1], [#3] K8s 状态与配置）。

**未知或需进一步排查的环节：**
现有证据仅确认了插件二进制文件的物理缺失，未查明其缺失的根本原因（例如：CNI 插件安装脚本执行失败、节点镜像未正确包含该插件、或管理该插件的 DaemonSet 部署失败/未滚动更新）。这些属于上游基础设施层面的故障原因，本次异常组诊断未能覆盖。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.7s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-v14/workload: 35.4s (Evidence 26.4s, RCA 8.9s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-sandbox-create-failed
