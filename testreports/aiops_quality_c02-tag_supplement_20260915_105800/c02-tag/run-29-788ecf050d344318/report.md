## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在远程仓库中不存在（404 NotFound），导致 kubelet 反复拉取失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `aiops-case-v07/workload` | 状态 `Pending`，阶段 `PodScheduled` (True) 但 `Ready` (False) | 确认 Pod 调度成功但启动失败 |
| 2 | K8s State | `aiops-case-v07/workload` | 容器 `app` 状态 `waiting`，原因 `ImagePullBackOff`，消息 "Back-off pulling image..." | 直接反映镜像拉取失败后的退避状态 |
| 3 | K8s Event | kubelet | 事件 `Failed` (Over 34m x6)：`rpc error: code = NotFound desc = failed to pull and unpack image ... pause:aiops-fixture-unavailable-20260908: not found` | 核心故障证据，明确指出镜像 Tag 不存在 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason: ImagePullBackOff) 采样值 `1` | 从监控侧确认容器持续处于拉取失败状态 |

**证据小结**：
K8s 事件 `fact-2217fd7a557f` 直接揭示了远程仓库返回 404 (NotFound) 的根本原因。K8s 状态 `fact-ed9ce5e214db` 与 Prometheus 指标 `fact-2de0cec98385` 均证实容器从 `ErrImagePull` 进入了 `ImagePullBackOff` 状态，这与事件序列（拉取失败 → 退避）完全一致，排除了集群资源不足等其他启动失败因素。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 Tag 不存在 (NotFound) → kubelet 拉取失败 (rpc error) → Pod 进入 ImagePullBackOff 退避状态 → Pod 持续 Pending，容器未运行
```

### 根因结论

已确认的根因是工作负载 `aiops-case-v07/workload` 配置的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在（返回 404 NotFound）。

该直接原因导致 kubelet 在拉取镜像时失败，Pod 状态由 `Pending` 进入 `ImagePullBackOff` 并持续重试退避（见证据 1、2、3），最终表现为应用容器无法启动（见证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 10.4s
├─ 并发证据采集: 46.6s
│  └─ g1 aiops-case-v07/workload: 46.6s (Evidence 37.9s, RCA 8.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
