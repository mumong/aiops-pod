## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 持续处于 ImagePullBackOff 状态，容器 app 未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed ... Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` | 直接指明拉取指定镜像标签失败的原因为仓库端返回 `NotFound` |
| 2 | K8s Event | kubernetes | `BackOff ... Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 证实 kubelet 在连续拉取失败后已进入指数退避重试状态 |
| 3 | K8s Config | kubernetes | `container: app, resource_request.cpu: 5m; resource_request.memory: 8Mi` | 排除因资源申请量过小导致 Pod Pending 的可能性 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 独立确认容器当前确实处于 `ImagePullBackOff` 等待状态 |

事件记录中清晰的 `NotFound` 错误与 Metric 确认的退避状态互为印证，共同锁定故障原因为镜像仓库端不存在指定版本。由于容器未能启动，物理上未产生应用日志与业务 Tracing 数据。

## 🎯 根因分析 · g1

### 因果链

```text
仓库端镜像标签 'aiops-fixture-unavailable-20260908' 不存在 → 容器运行时拉取镜像返回 NotFound 错误 → kubelet 进入 ImagePullBackOff 退避重试 → Pod 状态持续为 Pending/ImagePullBackOff，应用未启动
```

### 根因结论

已确认的根因是 Pod 中 `app` 容器指定的镜像标签 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不存在。

该根因直接导致了拉取操作返回 `NotFound` 错误，进而触发 kubelet 的指数退避重试机制，使得 Pod 无法完成初始化。证据链由 K8s 事件原文的 `not found` 报错与 Prometheus 指标中 `ImagePullBackOff` 状态的独立观测共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 51.1s
├─ 问题定位: 15.7s
├─ 并发证据采集: 26.9s
│  └─ g1 aiops-case-v07/workload: 26.9s (Evidence 19.7s, RCA 7.1s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
