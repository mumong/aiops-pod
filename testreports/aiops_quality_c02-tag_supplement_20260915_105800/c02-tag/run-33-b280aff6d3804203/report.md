## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，持续 Pending 且无重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: Pending | 确认 Pod 当前未进入运行状态 |
| 2 | K8s Event | kubernetes | Warning Failed (x4): Error: ErrImagePull | 提供初步拉取失败警告 |
| 3 | K8s Event | kubernetes | Warning Failed (x6): Error: ImagePullBackOff | 确认 kubelet 进入拉取重试退避状态 |
| 4 | K8s Event | kubernetes | Normal BackOff (x154): Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908" | 说明拉取动作正在持续重试且受阻 |
| 5 | K8s Event | kubernetes | Warning Failed: rpc error: code = NotFound desc = failed to resolve reference ...: not found | 明确镜像拉取失败的底层具体原因 |
| 6 | Metric | prometheus | kube_pod_container_status_waiting_reason=1 (reason: ImagePullBackOff) | 佐证 Pod 处于等待状态的原因 |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total=0 | 确认应用容器从未成功启动过 |

**证据说明：**
事件记录 (fact-4 至 fact-5) 直接提供了具体的错误代码 `NotFound` 和缺少的镜像引用路径，确证了拉取失败的根本原因；指标数据 (fact-6) 独立验证了容器状态为 `ImagePullBackOff`，与 Kubernetes 状态事实 (fact-1) 完全一致；重启计数 (fact-7) 排除了应用崩溃重启的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库中 tag 'aiops-fixture-unavailable-20260908' 不存在 → kubelet 拉取镜像失败 (NotFound) → Pod 持续处于 ImagePullBackOff 状态 → 应用服务不可用 (Pending)
```

### 根因结论

已确认根因为**容器镜像 tag 不存在**。Kubernetes 事件记录 (fact-5) 明确指出镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不存在（code = NotFound），导致 `kubelet` 无法拉取并启动该镜像（fact-3），从而使 Pod 持续处于 `ImagePullBackOff` 状态（fact-1, fact-6），应用服务因此不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 56.0s
├─ 问题定位: 21.2s
├─ 并发证据采集: 26.0s
│  └─ g1 aiops-case-v07/workload: 26.0s (Evidence 18.1s, RCA 7.8s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
