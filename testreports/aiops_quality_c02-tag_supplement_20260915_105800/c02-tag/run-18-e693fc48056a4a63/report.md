## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload处于Pending状态，Container app状态为ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending`，`container.waiting_reason: ImagePullBackOff` | 确认 Pod 卡在初始化阶段，容器处于拉取镜像失败的等待状态 |
| 2 | K8s Event | kubernetes | `Warning Failed ... Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": rpc error: code = NotFound desc = ... not found` | 直接证明镜像仓库返回 404 错误，目标镜像标签在仓库中不存在 |
| 3 | K8s Event | kubernetes | `Normal BackOff ... Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 确认 kubelet 在多次拉取失败后已进入退避重试机制 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 量化反映容器因拉取失败而停滞，无重启（重启计数为 0） |

**证据链说明：**
Kubernetes 事件（证据 2, 3）明确指出镜像拉取失败的直接原因是 `NotFound`，结合容器等待状态（证据 1）和 Metric 指标（证据 4），三者共同证实故障由外部镜像仓库中的镜像缺失导致，而非集群资源或网络故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置引用了镜像tag `aiops-fixture-unavailable-20260908` → 该 tag 在阿里云镜像仓库中不存在(NotFound) → kubelet拉取失败并触发BackOff机制 → Pod因容器无法启动而卡在ImagePullBackOff/Pending状态，业务不可用
```

### 根因结论

已确认根因为 **镜像不存在（Image Tag Not Found）**。

故障证据链完整：Kubernetes 事件明确捕获了 `rpc error: code = NotFound desc = ... not found`（证据 #2），直接指向 Pod 配置中引用的特定镜像标签 `aiops-fixture-unavailable-20260908` 在仓库中缺失。这一错误导致容器无法启动，Pod 长期处于 `Pending` 阶段（证据 #1），且由于从未启动成功，Metric 显示重启计数为 0（证据 #4）。目前无需更多日志或追踪数据即可定界。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.8s
├─ 并发证据采集: 36.0s
│  └─ g1 aiops-case-v07/workload: 36.0s (Evidence 27.6s, RCA 8.2s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
