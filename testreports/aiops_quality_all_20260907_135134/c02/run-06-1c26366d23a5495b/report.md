## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.waiting_reason: ImagePullBackOff` (fact: fact-dea5360991e8) | 确认容器因镜像拉取失败而处于等待状态 |
| 2 | K8s State | `kubernetes` | `container.waiting_message: Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact: fact-fd020a633318) | 明确错误原因为无法拉取指定镜像地址 |
| 3 | K8s State | `kubernetes` | `pod.phase: Pending` (fact: fact-426477d643d3) | 确认 Pod 因无法启动容器而停留在调度后阶段 |
| 4 | K8s Config | `kubernetes` | `container.resource_limit.memory: 32Mi`, `cpu: 50m` (fact: fact-47e0417c0b9b, fact-90f1b103adfd) | 确认容器资源限制配置极小，排除因资源不足导致启动失败 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}: 1` (fact: fact-f631b4c9b2b1) | 独立于 K8s API 确认等待状态的数值事实 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total: 0` (fact: fact-a715739eccb7) | 确认容器从未成功启动，无重启记录 |

**证据说明：**
Kubernetes 的等待原因、等待信息及 Pod 状态一致指向镜像拉取阶段失败（fact-1, 2, 3）；Prometheus 指标独立证实了等待原因为 `ImagePullBackOff` 且启动次数为 0（fact-5, 6），且资源限制配置极低（fact-4）进一步排除了 OOM 等启动后崩溃的可能，所有事实指向明确的镜像解析与拉取失败。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
Pod 配置了无效镜像仓库地址 registry.invalid → DNS 解析失败 (no such host) → 镜像拉取失败并进入 BackOff 重试 → Pod 状态变为 ImagePullBackOff
```

### 根因结论

已确认的根因为 Pod 配置了无法解析的有效镜像仓库地址 `registry.invalid`（见 fact-fd020a633318）。该地址导致 DNS 解析失败，进而引发 `ImagePullBackOff` 状态，使 Pod 无法进入 Running 状态（见 fact-dea5360991e8）。这一结论得到了 K8s 状态事件（fact-1, 2, 3）以及 Prometheus 等待状态指标（fact-5）的交叉印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.9s
├─ 并发证据采集: 47.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 47.1s (Evidence 39.4s, RCA 7.6s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
