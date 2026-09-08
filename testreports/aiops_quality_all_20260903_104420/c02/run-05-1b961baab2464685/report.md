## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Error: ImagePullBackOff` (持续约 7m25s, 触发频率 x6) | 确认 Pod 处于最终重试等待状态 |
| 2 | K8s Event | `kubelet` | `Failed to pull image "registry.invalid/aiops/workload:missing"... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明网络层 DNS 解析完全失败，无法联系仓库 |
| 3 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1, labels: `reason=ErrImagePull` | 独立观测佐证等待原因确认为拉取错误 |
| 4 | K8s State | `pod.status` | `Pending` | 确认容器尚未调度至运行时启动，卡在镜像拉取前 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 0 | 确认 Pod 存活时间为 0，从未成功启动过 |

证据互相印证，一致指向镜像拉取环节的失败：事件与指标确认等待原因为拉取失败，事件中的 `no such host` 错误排除了网络中断或仓库宕机的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效的镜像仓库域名 registry.invalid → Kubelet DNS 解析失败 (no such host) → 镜像拉取失败触发 ErrImagePull → Pod 进入 ImagePullBackOff 状态
```

### 根因结论

已确认的根因是 Pod `aiops-case-02/workload-65b7f54794-rnlv4` 的镜像引用使用了保留域名 `registry.invalid`。Kubelet 在执行拉取操作时，DNS 解析彻底失败，无法发现主机名，导致镜像拉取永久失败并触发 `ImagePullBackOff` 机制。

关键支撑证据为 Kubelet 事件 (fact-15c29f181cb7, fact-6ce864eaf0e6) 直接报告了 `no such host` 错误，以及 Prometheus 指标 (fact-60d429aedaed) 确认 `ErrImagePull` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.3s
├─ 并发证据采集: 72.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 72.3s (Evidence 64.5s, RCA 7.7s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
