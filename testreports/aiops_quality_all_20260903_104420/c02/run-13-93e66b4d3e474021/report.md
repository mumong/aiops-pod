## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 Pending/ImagePullBackOff 状态，无法拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-1536f4fd764a) | 确证镜像域名 `registry.invalid` 解析失败，为 DNS 故障导致拉取失败的直接证据。 |
| 2 | K8s Event | kubernetes | `Error: ImagePullBackOff` (fact-f82f0facceef) | 描述 Pod 当前持续的等待状态，与 K8s State 的 `ImagePullBackOff` 一致。 |
| 3 | K8s State | kubernetes | `container.waiting_reason: "ImagePullBackOff"` (fact-41b24702a44d) | 反映容器当前的异常状态，确认 Pod 无法进入就绪阶段。 |
| 4 | K8s State | kubernetes | `pod.phase: "Pending"` (fact-4e0a1d723ec6) | 确认 Pod 停留在调度后的初始阶段，未开始运行。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason: 1` (labels: `reason=ImagePullBackOff`) (fact-0d1df41d43d4) | 独立监控维度印证 Pod 正处于镜像拉取失败的等待状态。 |

Kubernetes Event (fact-1536f4fd764a) 提供的 `lookup ... no such host` 错误原文揭示了镜像拉取失败的根本原因是网络解析失败，而非镜像本身不存在或认证失败。Metric 数据 (fact-0d1df41d43d4) 独立观测到了这一等待状态，证实了异常的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像配置了无效域名 registry.invalid → 域名解析失败 (lookup no such host) → 无法连接仓库拉取镜像 → ErrImagePull / ImagePullBackOff
```

### 根因结论

已确认根因：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 的镜像地址配置了无效的域名 `registry.invalid`，导致 kubelet 尝试解析该域名时发生 DNS 失败（`no such host`），无法建立网络连接并拉取镜像。

证据表明，`kubelet` 在尝试拉取镜像时，因域名无法解析直接报错（fact-1536f4fd764a）。这引发了 `ErrImagePull` 并最终进入 `ImagePullBackOff` 循环（fact-f82f0facceef, fact-0d1df41d43d4），导致 Pod 状态持续为 `Pending`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.8s
├─ 并发证据采集: 60.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 60.7s (Evidence 52.3s, RCA 8.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
