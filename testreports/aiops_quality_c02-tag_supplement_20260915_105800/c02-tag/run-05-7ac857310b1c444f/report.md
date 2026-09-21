## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload Pod 处于 ImagePullBackOff 状态，容器 app 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v07/workload` 状态为 `Pending`，容器 `app` 状态 `ImagePullBackOff`，重启次数 0 | 确认容器处于拉取镜像失败后的退避阶段，未进入运行态 |
| 2 | K8s Event | Kubernetes | `Failed to pull image .../pause:aiops-fixture-unavailable-20260908`: rpc error: code = NotFound desc = failed to pull and unpack image...: not found | 提供根本原因的直接证据：远程仓库中该 Tag 对应的镜像层不存在 |
| 3 | K8s Event | Kubernetes | `Error: ErrImagePull` 持续 4m6s (x4)，`Back-off pulling image` 持续 5m39s (x22) | 证明拉取失败是持续发生的，且 kubelet 正在执行指数退避策略 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (label: reason=ImagePullBackOff) 值为 1 | 从监控维度独立印证了容器处于 ImagePullBackOff 状态 |

**证据总结：**
K8s State 与 Event 事实链完整，从状态（Pending/ImagePullBackOff）到具体报错（NotFound）再到行为表现（BackOff），逻辑闭环且互相印证。Metric 数据的 `reason=ImagePullBackOff` 标签与 K8s 事件描述一致，证实了该状态不是瞬时故障。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 Tag 'aiops-fixture-unavailable-20260908' 在仓库中不存在 → kubelet 执行拉取操作触发 NotFound 错误 → 拉取失败进入 BackOff 循环 → Pod 状态保持 ImagePullBackOff 且无法启动
```

### 根因结论

已确认根因为：Pod 定义中指定的镜像 Tag `aiops-fixture-unavailable-20260908` 在远程仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中并不存在（见证据 #2）。

该错误导致 kubelet 每次尝试拉取时均收到 `NotFound` 响应，由于无法获取合法的镜像层，容器无法初始化，进而触发 K8s 的退避机制（BackOff）以避免频繁重试。这与观测到的 `ImagePullBackOff` 状态和事件完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 55.1s
├─ 问题定位: 11.6s
├─ 并发证据采集: 34.9s
│  └─ g1 aiops-case-v07/workload: 34.9s (Evidence 26.4s, RCA 8.2s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
