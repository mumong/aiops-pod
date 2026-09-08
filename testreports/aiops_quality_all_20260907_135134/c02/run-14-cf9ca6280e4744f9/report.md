## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置的镜像地址 registry.invalid/aiops/workload:missing 使用了无效的 TLD 域名 (.invalid)，导致 kubelet 无法通过集群 DNS (127.0.0.53) 解析镜像仓库主机名，从而无法拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-8230c877be1e) | 核心证据。证实 kubelet 尝试解析镜像地址时，因 TLD `.invalid` 在集群 DNS 中无定义而彻底失败。 |
| 2 | K8s State | kubernetes | `ImagePullBackOff` (fact-c972c7b33a9c) / 容器状态 `Waiting` (fact-d0107732caa9) | 症状确认。表明 Pod 进入等待状态且已触发重试退避，验证拉取操作不仅失败且处于持续重试/失败循环中。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-4a48068887ad) | 独立观测。Prometheus 指标直接映射到具体的 ImagePullBackOff 原因，佐证 K8s 事件中的错误状态。 |
| 4 | K8s State | kubernetes | `pod.status.phase = Pending` (fact-7c88ae40eea2) | 运行态确认。Pod 因镜像未拉取成功，始终无法进入 Succeeded 或 Running 阶段，符合拉取失败的预期状态。 |

K8s 事件中的 DNS 解析失败记录 (fact-1, 事实来源为 kubelet 底层报错) 是故障的直接证据，它同时解释了 Metric 观测到的 `ImagePullBackOff` 等待状态 (fact-3) 以及 K8s 容器的 `ImagePullBackOff` 原因 (fact-2)。由于容器从未成功启动，Logging 和 Tracing 维度无数据符合预期，K8s 事实构成了完整且自洽的证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像地址使用了无效的 TLD 域名 (.invalid) → kubelet 解析镜像仓库主机名失败 (no such host) → 镜像拉取操作彻底失败 → 容器进入 ImagePullBackOff 状态，Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 配置了无效的镜像地址** (`registry.invalid/aiops/workload:missing`)。

该地址使用了保留域名 `.invalid`，导致 kubelet 尝试通过集群 DNS (127.0.0.53) 解析该主机名时，返回 `no such host` 错误 (见证据表 #1)。这一网络层级的解析失败直接阻断了镜像的下载，致使容器无法启动并持续重试，最终表现为 `ImagePullBackOff` (见证据表 #2) 和 `Pending` 状态 (见证据表 #4)，Metric 层面的 `kube_pod_container_status_waiting_reason` 为 `ImagePullBackOff` (见证据表 #3) 进一步确认了该现象。证据充分且指向明确，日志与追踪数据的缺失系容器未启动的自然结果，不构成证据缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.7s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 40.0s (Evidence 34.5s, RCA 5.4s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
