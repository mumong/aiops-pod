## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod 配置使用了无效的镜像仓库域名 `registry.invalid`，导致 Kubelet 执行 DNS 解析失败（`no such host`），无法拉取镜像并持续重试进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Pending` (`fact-0cf594bb1f87`) | 明确 Pod 当前生命周期状态 |
| 2 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing"... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (`fact-115fe132ffb3`) | 揭示容器镜像拉取失败的具体网络与 DNS 错误 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ImagePullBackOff` (`fact-dbe9abca035d`) | 确认容器等待状态为镜像拉取退避 |
| 4 | K8s Config | Kubernetes | `image: "registry.invalid/aiops/workload:missing"` (源自 `failed to pull image "registry.invalid/aiops/workload:missing"` 事件) | 指出配置中使用的具体无效域名与镜像名 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` value: `1` with reason `ImagePullBackOff` (`fact-214ad9581b4a`) | 从监控系统侧独立确认容器处于 ImagePullBackOff 状态 |

**证据互证说明：**
Kubernetes 事件（#2）精确记录了 DNS 解析失败（`no such host`）并直接关联到配置中的无效域名（#4），同时 K8s State（#1, #3）确认了由此引发的 Pending 与 ImagePullBackOff 状态；Prometheus 监控指标（#5）在同一时间窗口内独立验证了该等待状态的存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置使用了无效域名 `registry.invalid` 作为镜像仓库 → Kubelet 执行 DNS 解析失败 (`no such host`) → 无法拉取镜像并持续重试 → Pod 进入 ImagePullBackOff 状态
```

### 根因结论

已确认根因为 Pod 配置中使用了无效的镜像仓库域名 `registry.invalid`。
该配置导致 Kubelet 在尝试拉取 `registry.invalid/aiops/workload:missing` 时发生 DNS 解析失败（错误原文见证据 #2），无法获取容器镜像，进而触发 Kubelet 的退避拉取逻辑，使 Pod 卡在 `ImagePullBackOff` 状态（见证据 #3, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 22.2s
├─ 并发证据采集: 82.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 82.0s (Evidence 75.9s, RCA 5.9s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
