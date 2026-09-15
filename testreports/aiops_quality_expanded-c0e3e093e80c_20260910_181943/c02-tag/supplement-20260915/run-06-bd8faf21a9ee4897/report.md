## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，持续 Pending 未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed: Error: ErrImagePull` (x6 over 6m45s) | 确认可视故障现象为镜像拉取失败 |
| 2 | K8s Event | Kubernetes | `Error: ImagePullBackOff` (x4 over 6m45s); Failed to pull image "...: not found" | 明确指出拉取 `pause:aiops-fixture-unavailable-20260908` 时收到 `NotFound` |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi`; `limit: 32Mi`; `cpu: 5m/50m` | 排除因资源限制导致的启动失败 |
| 4 | K8s State | Kubernetes | `status: Pending`; `restart_count: 0` | 确认 Pod 因未拉起容器而持续 Pending，且无重启循环 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 独立确认 Pod 处于 `ImagePullBackOff` 等待状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 验证容器从未启动过，排除启动后崩溃因素 |

**证据说明：**
1. **因果闭环**：K8s Event (#2) 直接捕获了远程仓库返回的 `NotFound` 错误，解释了 K8s Event (#1) 中的 `ErrImagePull` 现象，并确认了状态机流转至 `ImagePullBackOff` 的直接原因。
2. **状态互证**：Metric 观测 (#5, #6) 独立证实了 Pod 处于“等待”且“无重启”的状态，与 K8s State (#4) 描述的 `Pending` 及 `restart_count: 0` 一致，排除了资源瓶颈或容器崩溃的可能。
3. **配置排除**：K8s Config (#3) 展示了合理的资源配额，且因容器未启动，Logging/Tracing 维度无数据是符合物理预期的，无需额外排查。

## 🎯 根因分析 · g1

### 因果链
```text
镜像 tag 不存在于仓库 → kubelet 拉取镜像时收到 404/NotFound 响应 → 容器启动失败并进入 ErrImagePull -> ImagePullBackOff 状态 → Pod 保持 Pending 状态，无容器启动日志或链路
```

### 根因结论
**已确认根因：Pod 配置引用的容器镜像标签不存在。**

证据显示 (见证据 #2)，`aiops-case-v07/workload` 尝试拉取的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中未找到（`not found`）。这导致 `kubelet` 拉取失败，Pod 进入指数退避等待的 `ImagePullBackOff` 状态，进而表现为 `Pending` 且无后续运行日志 (见证据 #1, #4, #5)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.7s
├─ 并发证据采集: 42.1s
│  └─ g1 aiops-case-v07/workload: 42.1s (Evidence 33.0s, RCA 8.9s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
