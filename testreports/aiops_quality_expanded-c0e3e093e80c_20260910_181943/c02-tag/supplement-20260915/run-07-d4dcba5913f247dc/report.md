## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod workload in aiops-case-v07 is stuck in ImagePullBackOff (Pending). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": rpc error: code = NotFound desc = failed to pull ... not found` | 明确指向镜像拉取失败的具体错误原因（镜像不存在） |
| 2 | K8s Event | kubelet | `Normal BackOff ... Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 佐证拉取失败后 kubelet 的重试退避行为 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `container="app", reason="ImagePullBackOff"`) | 从监控维度确认容器正处于 ImagePullBackOff 状态 |
| 4 | K8s State | kubernetes | `pod.status: Pending` (fact-73eee52c53d2) | 展示 Pod 整体状态因容器无法启动而停留在 Pending |

**证据印证说明：**
Kubernetes 事件明确指出无法解析镜像 tag (`aiops-fixture-unavailable-20260908`)，返回 `NotFound` 错误（证据1）。这解释了为什么容器处于 `ImagePullBackOff` 状态（证据2），并被 Prometheus 监控指标确认（证据3）。Pod 因容器无法启动而停留在 `Pending` 状态（证据4），整个证据链闭环验证了镜像不可用的根因。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 'aiops-fixture-unavailable-20260908' 不存在 → Kubelet 拉取镜像报 'NotFound' 错误 → 容器卡在 ImagePullBackOff 状态 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因：** 容器运行时配置引用的镜像 tag (`aiops-fixture-unavailable-20260908`) 在指定 registry (`registry.cn-hangzhou.aliyuncs.com/google_containers/pause`) 中不存在。

**证据引用：** 该根因由 kubelet 返回的具体 `rpc error: code = NotFound` 事实直接支撑（证据 #1），并得到 `ImagePullBackOff` 监控状态（证据 #3）的佐证。现象完全由镜像拉取失败机制导致，排除了网络、权限或其他资源限制问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.9s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-v07/workload: 45.0s (Evidence 35.3s, RCA 9.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
