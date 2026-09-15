## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 镜像 registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908 在仓库中不存在 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `Pending` | 确认 Pod 尚未成功运行 |
| 2 | K8s Event | kubelet (Warning) | `Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... not found` | 根本证据：镜像仓库明确拒绝拉取，返回 NotFound |
| 3 | K8s Event | kubelet (Warning/Normal) | `Error: ErrImagePull` 及连续 `BackOff pulling image` | 确认系统正反复尝试拉取同一不可用镜像并退避 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 指标观测与 Kubernetes 事件状态完全一致 |

**证据关联分析：**
- K8s 事件 `fact-7296edd05e68` 提供了决定性的失败原因（仓库 404 NotFound），排除了网络超时或认证失败。
- Metric `fact-a965691afaed` 证实了当前容器状态确实处于 ImagePullBackOff，且因单次采样未展示持续爬升趋势，故以当前状态事实为准。
- Pod 资源配置 (`fact-21c39205930c`, `fact-41ee0b66d86a`) 和重启次数 (`fact-d89d69fef4b6`) 属于无关上下文，证实了异常非资源耗尽或崩溃重启引起。

## 🎯 根因分析 · g1

### 因果链
```text
目标镜像标签不存在 → kubelet 拉取时被 Registry 拒绝 (NotFound) → 镜像拉取失败，容器无法启动 → Pod 停留在 Pending 并抛出 ImagePullBackOff 事件
```

### 根因结论
已确认的根因为**目标镜像在仓库中不存在**。
具体而言，Pod 配置请求的镜像标签 `aiops-fixture-unavailable-20260908` 在 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 仓库中找不到（证据：`fact-7296edd05e68`）。这一直接原因导致了容器拉取失败，进而触发了 `ImagePullBackOff` 状态（证据：`fact-26c81bd22093`, `fact-a965691afaed`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 26.8s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-v07/workload: 32.3s (Evidence 24.5s, RCA 7.6s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
