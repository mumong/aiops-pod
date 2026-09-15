## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: code = Unknown desc = ... Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-2c03846b801b) | 核心证据：直接指明 DNS 解析失败导致网络请求中断 |
| 2 | K8s Event | kubernetes | `Error: ErrImagePull` (fact-dd5f74350bd4) | 初始失败状态，由上述网络/解析错误触发 |
| 3 | K8s Event | kubernetes | `Error: ImagePullBackOff` (fact-3b2edda3aaae) | 失败后的重试退避状态，确认拉取动作被系统阻止 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, labels: `reason: ImagePullBackOff` (fact-9f7fd0f2cd25) | 独立指标确认 Pod 处于等待拉取镜像的阻塞状态 |
| 5 | K8s State | kubernetes | Pod `pending` (fact-b65ae54fa75f) | 容器未启动导致 Pod 生命周期停留在 Pending 阶段 |

**证据印证说明**：
Kubernetes 事件 `fact-2c03846b801b` 明确指出 `registry.invalid` 域名在 DNS 解析时返回 `no such host`，这直接解释了为何 `ErrImagePull` (fact-dd5f74350bd4) 随后发生，并最终进入 `ImagePullBackOff` (fact-3b2edda3aaae) 状态。Prometheus 指标 `fact-9f7fd0f2cd25` 中的 `waiting_reason` 为 `ImagePullBackOff`，与 K8s 事件状态完全一致，证实了拉取行为因镜像配置问题被持续阻断。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效域名 registry.invalid 的镜像地址 → DNS 解析失败 (no such host) → 镜像拉取请求网络中断 → Pod 处于 Pending/Waiting (ImagePullBackOff) 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-02/workload-65b7f54794-z7kdp` 的镜像配置引用了一个在集群网络中无法解析的域名 `registry.invalid`。
- **证据支撑**：K8s Event `fact-2c03846b801b` 记录到 kubelet 尝试解析该域名时明确返回 "no such host"，且该错误导致了后续一连串的拉取失败事件 (fact-2c03846b801b, fact-dd5f74350bd4, fact-3b2edda3aaae)。
- **结论**：由于镜像注册表地址配置错误（或 DNS 记录缺失），导致 kubelet 无法建立连接拉取镜像，进而引发 Pod 无法启动。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 17.9s
├─ 并发证据采集: 555.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 555.9s (Evidence 548.0s, RCA 7.9s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
