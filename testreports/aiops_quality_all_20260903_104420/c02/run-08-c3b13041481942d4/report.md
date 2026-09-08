## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-013837170e34` | container.waiting_reason: ImagePullBackOff | 直接证明当前 Pod 处于镜像拉取失败且正在退避重试的状态 |
| 2 | K8s Event | `fact-26a27f9c5893` | kubelet 报错: failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host | 确认了失败的确切机制：集群 DNS 无法解析 registry.invalid 域名，导致镜像拉取被拒绝 |
| 3 | K8s Event | `fact-06d25ed37ee4` | kubelet 报告: Back-off pulling image "registry.invalid/aiops/workload:missing" | 反映了 kubelet 对无法拉取镜像的持续重试行为模式，证实了故障的持续性 |
| 4 | Metric | `fact-c00023d719af` | kube_pod_container_status_waiting_reason=1 (reason=ImagePullBackOff) | 通过监控指标独立印证了 Pod 容器当前处于 ImagePullBackOff 等待状态 |
| 5 | K8s Config | (Context) | 容器 app 配置请求/限制 CPU 5m/50m，Memory 8Mi/32Mi | 作为系统运行资源配置的基线上下文，与此次 DNS 解析失败的根因无直接因果关系 |

**证据关系说明：**
Metric 数据与 K8s Event 均指向 ImagePullBackOff 状态，二者互为印证；Event 中 `no such host` 的报错文本直接锁定了 DNS 解析失败这一核心故障环节，证据链闭环完整。

## 🎯 根因分析 · g1

### 因果链

```text
镜像引用指向无效域名 registry.invalid → 集群 DNS (127.0.0.53) 解析失败 (no such host) → kubelet 拉取镜像被拒绝 (ErrImagePull) → Pod 持续重试并进入退避状态 (ImagePullBackOff)
```

### 根因结论

已确认根因为**Pod 配置了不存在的镜像仓库域名 `registry.invalid`，且集群 DNS 无法解析该域名**。

事实依据如下：
- **Kubernetes Event (`fact-26a27f9c5893`)** 提供了决定性的报错原文，明确指出尝试访问 `https://registry.invalid/v2/...` 时发生了 `dial tcp: lookup registry.invalid ... no such host`，证实了 DNS 解析失败。
- **Container Waiting Reason (`fact-013837170e34`)** 与 **Prometheus Metric (`fact-c00023d719af`)** 一致确认了容器因拉取镜像失败而进入了 ImagePullBackOff 状态。
- 日志与追踪数据因容器未启动而物理上不可用，但这并不影响基于 K8s 底层状态与事件数据的定论，已有事实完全支撑上述结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 35.1s
├─ 并发证据采集: 77.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 77.2s (Evidence 69.1s, RCA 8.0s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
