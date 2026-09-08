## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-02/workload-65b7f54794-rnlv4` | `phase: Pending`, `condition: Ready(False, ContainersNotReady)` | 确认 Pod 处于待调度/等待状态，无法就绪 |
| 2 | K8s Event | Kubelet | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认拉取行为发生，且处于退避等待阶段 |
| 3 | K8s Event | Kubelet | `Failed to pull image ...: dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认为核心诊断事实，直接指向 DNS 解析失败 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `reason: "ImagePullBackOff"` (value: 1) | 量化验证了容器等待原因与 Kubernetes 事件一致 |
| 5 | Metric | `kube_pod_container_status_restarts_total` | `0` | 确认容器从未成功启动，排除 OOMKill 等运行时退出因素 |
| 6 | K8s Config | Pod Definition | `container "app" resource_request: cpu=5m, memory=8Mi; resource_limit: cpu=50m, memory=32Mi` | 排除资源不足导致的调度失败或容器终止风险 |

证据表明，Pod 未能启动的原因完全归结于镜像拉取阶段。Metric 数据从侧面确认了集群当前只有等待状态而无运行实例；Kubelet 的 Event 日志提供了唯一的故障机理证据——集群内部 DNS (127.0.0.53) 无法解析域名 `registry.invalid`。由于容器从未启动，Logging 和 Tracing 维度的缺失（由采集工具权限拒绝导致）符合预期，不影响对网络/DNS 侧故障的定论。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS (127.0.0.53) 无 'registry.invalid' 解析记录 → Kubelet 尝试拉取镜像时发生 DNS 解析失败 → 容器持续处于 ImagePullBackOff 等待状态 → Pod 无法就绪，处于 Pending 状态
```

### 根因结论

**已确认根因：Kubernetes 集群内部 DNS 无法解析镜像仓库域名。**

依据证据 #3，Kubelet 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时，明确反馈了 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` 错误。这直接证实了 Pod 因 DNS 解析失败而无法获取镜像，进而触发 `ImagePullBackOff` 机制（证据 #2, #4），导致 Pod 永远停留在 `Pending` 状态（证据 #1）。

**遗留未知项：**
1. 域名 `registry.invalid` 是否为预期内的内部域名，或者是否为拼写错误。
2. 集群 DNS (CoreDNS/127.0.0.53) 是否因上游配置错误导致特定域名无法解析。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 21.6s
├─ 并发证据采集: 75.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 75.4s (Evidence 66.1s, RCA 9.1s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
