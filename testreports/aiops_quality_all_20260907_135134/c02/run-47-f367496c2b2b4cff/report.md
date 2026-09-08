## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 Pending 状态且 ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed 58m (x4 over 60m) kubelet Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: code = Unknown desc = ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 核心异常事实。证明 kubelet 无法解析 `registry.invalid` 域名，导致拉取镜像失败。 |
| 2 | K8s Event | kubernetes | `Warning Failed 58m (x6 over 60m) kubelet Error: ImagePullBackOff` | 确认容器因镜像拉取失败进入 BackOff 状态，验证了事件 1 的持续影响。 |
| 3 | K8s State | kubernetes | `pod.phase`: Pending; `pod.condition.ContainersReady`: False | 证实 Pod 处于待调度状态，容器未就绪，与事件事实一致。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` value: `1` (labels: `container="app"`, `reason="ImagePullBackOff"`), sample_count: 1 | 独立观测证实容器 `app` 确实处于 `ImagePullBackOff` 等待状态，支持根因分析。 |

**证据印证说明：**
Kubernetes 事件（#1, #2）与 Prometheus 指标（#4）交叉印证了 `ImagePullBackOff` 状态。事件中的 DNS 解析报错（#1）直接解释了为何无法拉取镜像（`registry.invalid`），指标仅确认了最终状态（#4），未提供额外排查维度。日志与 Tracing 因容器未启动而无法采集。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS (127.0.0.53) 中不存在域名 `registry.invalid` 记录 → kubelet 无法解析镜像仓库地址建立 HTTP 连接 → 拉取镜像失败并进入 Back-off 状态 → Pod 持续处于 ImagePullBackOff 异常状态
```

### 根因结论

已确认的根因为**镜像仓库域名无效**。Pod `aiops-case-02/workload-65b7f54794-nqrzv` 配置了使用 `registry.invalid` 的容器镜像，但集群 DNS 无法解析该域名（`no such host`），导致 kubelet 在拉取镜像时连接失败。此结论得到 Kubernetes 事件事实（Fact 1, 2）的强力支持，Metric 事实（Fact 4）提供了该状态的独立确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 41.9s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 38.2s (Evidence 31.3s, RCA 6.7s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
