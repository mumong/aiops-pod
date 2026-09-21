## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ErrImagePull | aiops-case-v07/workload Pod 处于 ErrImagePull/ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: ImagePullBackOff` 及 `Back-off pulling image` (fact-5e2a4932c49d) | 确认 Pod 处于镜像拉取重试退避状态 |
| 2 | K8s Event | kubernetes | `rpc error: code = NotFound desc = ... not found` (fact-93f3c42025e9) | 直接记录远程仓库返回的 404 错误，指向镜像不存在 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason=`ImagePullBackOff` (fact-fcd0ea49949c) | 监控指标与 K8s Event 的 BackOff 状态吻合 |

**证据说明：**
*   **1** 与 **3** 相互印证，确认容器当前状态稳定在 `ImagePullBackOff`，排除了短暂的网络抖动。
*   **2** 是决定性证据，Kubelet 明确收到仓库返回的 `NotFound` 错误，直接证实了镜像引用无效。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 配置了不存在的镜像 tag 'aiops-fixture-unavailable-20260908' → 远程仓库返回 NotFound 错误 → Kubelet 拉取失败触发 ErrImagePull 及重试退避 → Pod 持续处于 Pending 状态，未分配容器进程
```

### 根因结论
*   **已确认的根因**：Pod `aiops-case-v07/workload` 引用的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在（[证据 #2](#1)）。
*   **现象关联**：该镜像拉取失败直接导致了 [Kubelet Event](#1) 中的 `ImagePullBackOff` 以及 [Prometheus 监控](#3) 中 `waiting_reason=ImagePullBackOff` 为 1 的状态，导致 Pod 无法进入运行态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.4s
├─ 并发证据采集: 48.8s
│  └─ g1 aiops-case-v07/workload: 48.8s (Evidence 38.4s, RCA 10.2s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
