## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod `aiops-case-v07/workload` 处于 `ImagePullBackOff` 状态，未能启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ImagePullBackOff` (Fact: fact-6faf33231213, 29m 内 6 次) | 直接展示 Pod 处于 `ImagePullBackOff` 状态 |
| 2 | K8s Event | kubelet | `rpc error: code = NotFound ... pause:aiops-fixture-unavailable-20260908: not found` (Fact: fact-9e9dbb7fb058, 29m 内 4 次) | 证实容器镜像引用 `aiops-fixture-unavailable-20260908` 在仓库中不存在，是失败的根本原因 |
| 3 | K8s State | kubelet | `container.waiting_reason: ImagePullBackOff` (Fact: fact-c502a228d435, container: app) | 确认应用容器 `app` 等待拉取镜像的具体原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1，reason=`ImagePullBackOff`, container=`app` (Fact: fact-7d2232a07ad8) | 监控数据验证容器当前正处于镜像拉取失败的等待状态 |

**证据说明：**
- K8s 事件 `fact-9e9dbb7fb058` 明确记录了“NotFound”错误，证实镜像 `aiops-fixture-unavailable-20260908` 不存在，是 `ImagePullBackOff` 的直接原因。
- K8s 状态 `fact-c502a228d435` 与 Metric `fact-7d2232a07ad8` 分别从 Kubernetes API 和 Prometheus 确认了 Pod 容器正处于等待拉取镜像的状态。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 不存在 (NotFound) → kubelet 拉取失败 (ErrImagePull) → 指数退避重试 (ImagePullBackOff) → Pod 持续 Pending，不可用
```

### 根因结论

已确认根因：容器 `app` 配置引用的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不存在（`NotFound`），导致 kubelet 无法拉取该镜像。
- **证据支持**：`fact-9e9dbb7fb058` (K8s Event) 明确指出镜像未找到；`fact-6faf33231213` (K8s Event) 和 `fact-c502a228d435` (K8s State) 显示由于拉取失败触发了指数退避，Pod 处于 `ImagePullBackOff` 状态。
- **未确认项**：为何该特定 fixture 镜像 tag 在仓库中不存在（可能是配置错误，或是上游发布失败）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 11.5s
├─ 并发证据采集: 103.0s
│  └─ g1 aiops-case-v07/workload: 103.0s (Evidence 93.7s, RCA 9.1s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
