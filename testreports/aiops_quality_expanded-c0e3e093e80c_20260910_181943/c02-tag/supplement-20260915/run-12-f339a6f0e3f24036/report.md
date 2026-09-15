## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload Pod status is ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (kubelet) | `Error: ImagePullBackOff` / `rpc error: code = NotFound` | 确认容器镜像拉取因远程注册表返回 NotFound 失败，引发 Pod 异常 |
| 2 | K8s Event | kubernetes (kubelet) | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 显示 kubelet 正在重试拉取镜像，处于指数退避状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff", container="app"} = 1` | 从监控维度量化确认应用容器因镜像拉取失败处于等待状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` | 确认容器未发生过重启，进一步佐证 Pod 卡死在拉取阶段 |
| 5 | K8s State | kubernetes | `pod.status = Pending` | 确认 Pod 当前调度/启动状态被阻滞在 Pending 阶段 |

**证据关联说明**：
Kubernetes 事件（#1, #2）明确指出了故障原因为远程注册表返回 NotFound，这是直接原因。监控指标（#3, #4）在宏观数据层面验证了这一现象，排除了启动后崩溃重启（Restarts=0）的可能性。Pod 状态（#5）是上述拉取失败导致的最终滞留状态。

## 🎯 根因分析 · g1

### 因果链
```text
镜像 tag 'aiops-fixture-unavailable-20260908' 在远程注册表中不存在 → Kubelet 拉取镜像遭遇 NotFound 错误 → 容器启动失败并触发指数退避重试 → Pod 滞留于 Pending 且状态显示为 ImagePullBackOff
```

### 根因结论
已确认根因：指定的容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程注册表中不存在（NotFound）。该事实由 kubelet 的事件报错（fact-1c64b1b7a6bb, fact-dfa5b4ba3248）及 Metric 等待状态（fact-4df9700fb855）共同证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 26.0s
├─ 并发证据采集: 31.0s
│  └─ g1 aiops-case-v07/workload: 31.0s (Evidence 22.6s, RCA 8.2s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
