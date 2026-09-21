## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 Pending 状态，容器 app 因 ImagePullBackOff 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: Pending | 确认 Pod 整体停留在调度后/启动前阶段 |
| 2 | K8s Event | kubernetes | Warning Failed: ImagePullBackOff; kubelet 连续 6 次报告拉取失败 | 直接展示启动失败的核心异常信号 |
| 3 | K8s Event | kubernetes | Warning Failed: Failed to pull image: rpc error: code = NotFound desc = ...: not found | 明确指向镜像解析阶段的 NotFound 错误 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason=1 (reason=ImagePullBackOff, sample_count=1) | 独立量化观测到容器持续处于等待拉取状态 |

当前阶段 Pod 尚未成功启动，因此 Logging 与 Tracing 维度因无运行容器而处于 `not_applicable` 状态，无额外应用层证据。

**证据关联说明**：
1. **状态与事件印证**：K8s 状态确认 Pod 停留在 `Pending`（证据 #1），且该状态由连续的拉取失败事件驱动（证据 #2, #3）。
2. **错误根因锁定**：K8s 事件明确给出了 `NotFound` 的底层 RPC 错误（证据 #3），直接解释了为何状态持续为 `ImagePullBackOff`，无需通过指标进行时序趋势推断（证据 #4 为单样本，仅确认当前状态存在）。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 'aiops-fixture-unavailable-20260908' 在仓库 registry.cn-hangzhou.aliyuncs.com/google_containers/pause 中不存在 (k8s event: NotFound) 
→ kubelet 执行镜像拉取并收到仓库返回的 rpc error: code = NotFound 
→ 容器进入 ImagePullBackOff 状态，Pod 持续停留在 Pending 且未就绪 (k8s state: ContainersNotReady) 
→ 用户观察到 Pod 无法启动且处于等待状态
```

### 根因结论

**已确认的根因**：Pod 配置的容器镜像标签 `aiops-fixture-unavailable-20260908` 在远程镜像仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中实际不存在。

该根因由以下事实链条直接支撑：
1. 镜像拉取过程触发了 K8s 事件的 `NotFound` 错误（`rpc error: code = NotFound`），证明远程仓库侧无此版本资源（证据 #3）。
2. 拉取失败导致容器状态长期滞留于 `ImagePullBackOff`，且未产生任何重启或运行指标（证据 #1, #2, #4）。

目前的诊断已足够支撑该结论；剩余未确认项仅为该标签是否为预期使用的正确标签或存在拼写错误，这属于配置层面的业务确认，不影响故障发生的物理根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.3s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-v07/workload: 39.8s (Evidence 31.5s, RCA 8.2s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
