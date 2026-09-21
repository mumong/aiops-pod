## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ErrImagePull | Pod aiops-case-v07/workload 处于 Pending 阶段，容器 app 状态为 ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | `rpc error: code = NotFound ... failed to resolve reference "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-1b904cc51f03) | 确认底层镜像拉取失败的具体错误原因。 |
| 2 | K8s Event | K8s | `Warning Failed 51m (x4 over 52m) kubelet Error: ErrImagePull` (fact-9df8ba8d27da) | 确认异常现象的持续性与频次。 |
| 3 | K8s State | K8s | `container.waiting_reason: ImagePullBackOff` (fact-5271fbfc108f) | 确认容器当前处于等待拉取镜像的状态。 |
| 4 | K8s State | K8s | `container.waiting_message: Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-d8e1038f7f15) | 描述容器具体的重试退避行为。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-31135c53490f) | 从监控维度独立确认容器正处于拉取失败退避状态。 |

**证据印证说明：**
证据 1 提供了镜像拉取失败的确切原因（NotFound），直接解释了证据 2、3、4 中的 `ErrImagePull` 和 `Back-off pulling image` 状态。证据 5 作为独立的监控指标，在时间上（fact-31135c53490f 为 03:51）晚于初始报错（02:07 左右），证实了该拉取失败状态在后续观测窗口内仍持续存在且未被系统自动修复。所有 Kubernetes 状态、事件与 Prometheus 指标在异常现象上完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
镜像 Tag 不存在 → kubelet 拉取镜像返回 NotFound → Pod 进入 ImagePullBackOff 状态 → Pod 卡在 Pending 阶段
```

### 根因结论

已确认的根因是 **Pod 配置中引用的容器镜像 Tag `'aiops-fixture-unavailable-20260908'` 在指定仓库（`registry.cn-hangzhou.aliyuncs.com/google_containers/pause`）中不存在**。

这一事实由底层 K8s 事件中的 `rpc error: code = NotFound`（事实 1）直接证实，并直接导致了容器反复拉取失败、触发指数退避重试（事实 3、4、5），最终使得 Pod 持续处于 `Pending` 且容器处于 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.3s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-v07/workload: 43.9s (Evidence 35.6s, RCA 8.2s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
