## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 指定的容器镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在远程镜像仓库中不存在（返回 NotFound 错误），导致 Kubelet 无法拉取镜像，Pod 持续处于 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Pending` (fact-5871115eb5d2) | 确认 Pod 未进入正常运行阶段，处于调度后挂起状态。 |
| 2 | K8s Event | kubernetes | `ImagePullBackOff` (fact-dd14f929ee94), `Failed` (fact-0d6023f31c7f), `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-c837c12037ef) | 直接记录 Kubelet 拉取镜像失败后的重试与回退行为，证实故障持续存在。 |
| 3 | K8s Event | kubernetes | `Failed to pull image ...: failed to resolve reference ...: not found` (fact-acd2a8eade6d) | 提供底层网络与存储驱动的确切错误原因，指向镜像标签在仓库中不存在。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` (fact-fe26186eb2bc) | 从监控维度独立验证了容器等待原因为镜像拉取失败，与 K8s 事件结论一致。 |

K8s 事件日志详细记录了镜像拉取的失败细节，明确指出了具体的错误码（NotFound）。Metrics 数据通过独立的监控渠道确认了容器处于 `ImagePullBackOff` 状态。两者在故障现象与状态上完全吻合，共同支撑了镜像缺失的结论。Logging 和 Tracing 由于容器未启动而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
镜像标签 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在仓库中不存在(未确认) → Kubelet 解析镜像引用失败并返回 NotFound(已验证) → Pod 拉取镜像回退，状态变更为 ImagePullBackOff(已验证) → Pod 持续处于 Pending 状态(已验证)
```

### 根因结论

**已确认的根因：容器镜像在远程仓库中不存在。**

Kubelet 尝试拉取指定的容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 时，远程仓库返回了 `NotFound` 错误（证据 #3, fact-acd2a8eade6d）。这一事实导致 Kubelet 无法完成镜像下载，触发 `ImagePullBackOff` 机制（证据 #2, fact-dd14f929ee94；证据 #4, fact-fe26186eb2bc），最终使 Pod 处于 `Pending` 状态（证据 #1, fact-5871115eb5d2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.4s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-v07/workload: 33.4s (Evidence 26.3s, RCA 7.0s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
