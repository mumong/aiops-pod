## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason: "ErrImagePull"` (fact-4177fb4155ba) | 确认容器未启动的直接原因是镜像拉取失败 |
| 2 | K8s State | kubernetes | `container.waiting_message` 包含 `Head "https://registry.invalid/..." dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-f5cce68d210b) | 证实 DNS 解析失败是镜像拉取失败的根本机制 |
| 3 | K8s Event | kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-0e60c0029105) | 证实 kubelet 持续处于 BackOff 退避状态，符合 ErrImagePull 特征 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason="ImagePullBackOff"` (fact-0117f83beace) | 从监控侧独立确认了 Pod 处于 `ImagePullBackOff` 状态 |

日志与 Tracing 维度因目标容器未启动（ImagePullBackOff），物理上无法生成应用日志或业务 Trace；工具采集结果返回 `not_applicable` 或权限错误，故无相关证据。

**证据印证关系：**
Kubernetes 状态（fact-4177fb4155ba）与事件（fact-0e60c0029105）均指向同一终止状态 `ImagePullBackOff`，且失败信息（fact-f5cce68d210b）明确指向镜像域名 `registry.invalid` 的 DNS 解析失败；Prometheus 指标（fact-0117f83beace）进一步从系统层面独立印证了这一状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置使用了无效镜像域名 registry.invalid → kubelet 拉取镜像时 DNS 解析失败 (no such host) → 镜像拉取失败 (ErrImagePull) 并触发 BackOff 机制 → Pod 保持在 Pending/ImagePullBackOff 状态
```

### 根因结论

**已确认的根因：** Pod 配置镜像地址 `registry.invalid/aiops/workload:missing` 中包含无效域名 `registry.invalid`，导致 kubelet 在尝试拉取镜像时因 DNS 解析失败（`lookup registry.invalid ... no such host`）而持续报错并进入退避重试。

**证据支撑：**
- Kubernetes 状态事实 `fact-f5cce68d210b` 明确指出 Head 请求因 `no such host` 失败。
- Kubernetes 事件事实 `fact-0e60c0029105` 证实了 BackOff 现象。
- Prometheus 指标事实 `fact-0117f83beace` 确认了 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 33.8s
├─ 并发证据采集: 44.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 44.6s (Evidence 36.3s, RCA 8.1s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
