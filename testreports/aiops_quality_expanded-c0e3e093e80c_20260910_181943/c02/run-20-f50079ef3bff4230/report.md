## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod 配置的镜像仓库域名 'registry.invalid' 在集群 DNS (127.0.0.53) 中无法解析，导致 kubelet 无法拉取镜像 'registry.invalid/aiops/workload:missing'，引发持续 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Error: ErrImagePull` (fact-4122d495bf7a) | 记录首次拉取失败的警告事件，确立异常现象起点。 |
| 2 | K8s Event | kubelet | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-7d5985548022) | 提供决定性证据，精确到 DNS 解析失败和缺失的主机地址，直接指向根因。 |
| 3 | K8s Event | kubelet | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-a73f60487d37) | 确认 kubelet 正在进行重试退避，证明拉取动作被持续阻断，非瞬时错误。 |
| 4 | K8s Event | kubelet | `Warning Failed ... Error: ImagePullBackOff` (fact-e06bb04cbac7) | 标记最终进入 ImagePullBackOff 状态，与 Pod 状态维度一致。 |
| 5 | K8s State | pod.status | `status: Pending` (fact-20a62042b3a3) | 确认 Pod 因无法完成拉取而处于非运行状态。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `ImagePullBackOff`) (fact-b028d971e6a2) | 量化指标证实 Pod 处于 ImagePullBackOff 等待状态，且重启次数为 0。 |

上述证据互相印证：Kubernetes 事件 (fact-7d5985548022) 明确给出了 DNS `no such host` 的错误详情，直接解释了为何 Pod 处于 `Pending` 状态 (fact-20a62042b3a3) 并触发 Metric 观测到的 `ImagePullBackOff` 原因 (fact-b028d971e6a2)。由于容器未启动，Logging 和 Tracing 维度无实际数据，事件记录构成了完整的闭环证据链。

## 🎯 根因分析 · g1

### 因果链
```text
DNS 解析失败 (lookup registry.invalid on 127.0.0.53:53: no such host) → 镜像拉取被 kubelet 阻断 → Pod 状态转为 ImagePullBackOff → 应用不可用
```

### 根因结论
已确认的根因是 **Pod 配置的镜像仓库域名 `registry.invalid` 在集群 DNS (127.0.0.53) 中无法解析**。

这一网络配置错误导致 `kubelet` 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时遇到 `no such host` 错误，持续触发拉取失败和重试退避，最终使 Pod 维持在 `Pending` 和 `ImagePullBackOff` 状态。证据编号 2 (fact-7d5985548022) 提供了最直接的失败原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.3s
├─ 并发证据采集: 32.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 32.5s (Evidence 25.3s, RCA 7.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
