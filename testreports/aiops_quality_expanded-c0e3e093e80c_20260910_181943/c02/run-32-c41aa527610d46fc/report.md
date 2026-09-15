## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b (aiops-case-02) 处于 ImagePullBackOff 状态，容器 app 未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ErrImagePull` (fact-40eeb1105dd3) | 确认容器启动受阻，属于拉取阶段异常 |
| 2 | K8s Event | kubelet | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing"` (fact-6036b37fd73d) | 明确指出失败镜像及具体错误堆栈 |
| 3 | K8s Event | kubelet | `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-6036b37fd73d) | **决定性证据**：直接表明 DNS 解析失败，域名不存在 |
| 4 | K8s Event | kubelet | `Normal BackOff ... Back-off pulling image` (fact-a345f97edfde) | 显示 kubelet 正在重试，证实故障处于持续状态 |
| 5 | K8s State | pod.status | `Pending` (fact-b00b5a45f3f6) | 反映 Pod 调度成功但处于等待容器启动阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason: ImagePullBackOff` (fact-53085bcadbb8) | 独立于 K8s 事件，从指标侧确认容器持续处于 ImagePullBackOff 状态 |

**证据关联说明：**
K8s Event #3 提供了 `dial tcp: lookup ... no such host` 的确切技术原因，直接证明了 DNS 解析失败。Metric #6 确认了该状态的持续性，与 K8s Event #1 和 #3 共同构成了从指标到具体报错逻辑的闭环，排除了偶发性网络抖动的可能。

## 🎯 根因分析 · g1

### 因果链

```text
DNS解析失败 (域名 registry.invalid 不可达) → kubelet 镜像拉取机制阻断 → 容器处于 ImagePullBackOff 状态 → Pod 无法进入 Running 状态
```

### 根因结论

集群 DNS (127.0.0.53) 无法解析镜像仓库域名 `registry.invalid`，导致 kubelet 拉取镜像失败。

证据表明，kubelet 在执行镜像拉取时触发了 DNS 查询（见证据 #3），并收到了 `no such host` 响应。这一底层网络/配置故障直接导致了容器状态的停滞（见证据 #1、#6），构成了本次异常的确切根因。虽然未能提供具体的 DNS 配置错误原因（如 CoreDNS forward 配置缺失或域名拼写错误），但这不影响对“DNS解析导致拉取失败”这一事实链的确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.3s
├─ 并发证据采集: 32.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 32.5s (Evidence 22.8s, RCA 9.6s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
