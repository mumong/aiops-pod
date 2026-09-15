## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet (fact-6f1a061abb25) | `Failed to pull image "registry.invalid/aiops/workload:missing"`... `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认镜像拉取的直接失败机制是 DNS 解析失败，且域名 `registry.invalid` 无效 |
| 2 | K8s Event | kubelet (fact-606b058b9b5a, fact-8fad57548088) | `Error: ImagePullBackOff` (持续 59m, x6)；`Error: ErrImagePull` (持续 59m, x4) | 确认异常状态已稳定进入指数退避重试阶段，排除了瞬时网络抖动 |
| 3 | K8s State | kubelet (fact-4915b862cbf4) | Pod `Pending` (状态: `waiting`, reason: `ImagePullBackOff`) | 确认 Pod 处于调度后的等待阶段，容器尚未启动，验证了事实 #2 的最终表现 |
| 4 | Metric | Prometheus (fact-24ea67464177) | `kube_pod_container_status_waiting_reason` = 1 (labels: `container: app`, `reason: ImagePullBackOff`) | 从监控指标维度独立确认当前容器的等待原因与 K8s Event 保持一致 |

**证据交叉验证说明：**
*   **维度间一致性**：K8s Event（事实 #1, #2）记录的 DNS 错误细节，直接支撑了 Metric（事实 #4）中观察到的 `ImagePullBackOff` 等待状态，两者在异常归因上完全吻合。
*   **因果闭环**：DNS 解析失败（事实 #1）导致镜像拉取异常（事实 #2），进而使 Pod 状态维持在 Pending/Waiting（事实 #3），形成完整的故障现象链。由于容器无法启动，Logging 和 Tracing 维度确实无数据（输入中已明确标记 `not_applicable`），这排除了应用逻辑或启动后行为异常的可能性，将诊断焦点锁定在镜像拉取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了无效域名 registry.invalid → kubelet DNS 解析失败 (lookup registry.invalid: no such host) → 镜像拉取失败 (ErrImagePull -> ImagePullBackOff) → Pod 处于 ImagePullBackOff 状态
```

### 根因结论

**已确认的根因**：Pod 容器镜像配置（`registry.invalid/aiops/workload:missing`）包含无法解析的无效域名，导致 kubelet 在拉取镜像时遭遇 DNS 失败，从而陷入持续的拉取重试与 BackOff 状态。

该结论直接由输入事实 `fact-6f1a061abb25`（DNS 解析错误原文）和 `fact-24ea67464177`（等待原因为 ImagePullBackOff 的监控指标）共同支撑，因果链完整，无需补充其他维度的事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.8s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 39.9s (Evidence 30.1s, RCA 9.6s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
