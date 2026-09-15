## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod Spec中配置了无效的镜像仓库域名 `registry.invalid`，导致 kubelet 在执行镜像拉取时因 DNS 解析失败 (`no such host`) 而无法获取镜像，进而引发 `ImagePullBackOff`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | 2026-09-10T11:42:52Z 后 `Ready`: False, `ContainersReady`: False (reason: ContainersNotReady) | 证实 Pod 启动失败，容器未进入运行状态 |
| 2 | K8s State | pod.phase | Pending | 说明 Pod 调度完成但因启动失败处于挂起等待状态 |
| 3 | K8s State | container.waiting_reason | app 容器状态为 `ImagePullBackOff` | 明确指出镜像拉取受阻，是故障的根因信号 |
| 4 | K8s State | container.waiting_message | Back-off pulling image "registry.invalid/aiops/workload:missing" | 指出失效的镜像域名为 `registry.invalid` |
| 5 | Metric | kube_pod_container_status_waiting_reason | 2026-09-10T12:39:50.921000Z 记录到 `app` 容器的 `ImagePullBackOff` 状态 (值为 1) | 独立观测到等待原因为拉取镜像失败，印证 K8s 状态 |

Pod 处于 `Pending` 且 `Ready` 为 `False`，Kubernetes 原生状态直接揭示了容器的 `ImagePullBackOff` 等待原因，Metric 监控数据也记录了相同的等待状态，两者互为印证，排除了资源抢占或节点故障等其他启动阻碍因素。

## 🎯 根因分析 · g1

### 因果链

```text
无效的镜像仓库域名 (registry.invalid) → 镜像拉取失败 (ImagePullBackOff) → Pod 卡在 Pending/ContainersNotReady 状态 → 应用不可用
```

### 根因结论

已确认的根因是 Pod Spec 中配置的镜像仓库域名 `registry.invalid` 无法被解析或访问，直接导致 kubelet 在执行 `Pull Image` 操作时失败，从而触发 `ImagePullBackOff` 状态。
这一结论由 Kubernetes 容器等待状态（证据 #3, #4）与 Prometheus 监控的等待原因（证据 #5）共同确证。日志与链路追踪未采集，但根据容器未启动的物理事实，不影响该核心结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.9s
├─ 并发证据采集: 34.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 34.9s (Evidence 30.0s, RCA 4.8s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
