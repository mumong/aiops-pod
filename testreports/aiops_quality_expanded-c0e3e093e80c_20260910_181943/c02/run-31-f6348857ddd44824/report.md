## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: ... failed to do request: Head "https://registry.invalid/v2/...": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认 DNS 解析失败导致镜像拉取受阻的具体错误 |
| 2 | K8s Event | kubelet | `Warning Failed ... Error: ImagePullBackOff` | 确认 Pod 因拉取失败进入退避等待状态 |
| 3 | K8s State | kubelet | `Waiting Reason: ImagePullBackOff`, `Waiting Message: Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认容器当前具体的等待原因 |
| 4 | K8s State | kubelet | `Phase: Pending` | 确认 Pod 因容器状态异常而调度停留在 Pending 阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 独立印证 K8s State 中的 ImagePullBackOff 状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` | 排除应用因 OOM 或 CrashLoopBackOff 导致的重启 |

**证据印证说明：**
1. K8s Event 1 提供了决定性证据，明确指出 `registry.invalid` 域名解析失败。
2. K8s Event 2 与 Metric 5 分别从事件日志和时序数据侧面印证了容器当前正处于 ImagePullBackOff 状态。
3. Metric 6 确认重启次数为 0，排除了容器启动后因故障导致退避的可能。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid 配置错误 → DNS 解析失败 (lookup registry.invalid ... no such host) → 镜像拉取失败并指数退避 (ImagePullBackOff) → Pod 状态维持为 Pending 及 ImagePullBackOff
```

### 根因结论

已确认根因为 Pod 配置了无效的镜像仓库域名 `registry.invalid`。

该域名无法被解析（事实 1），导致 kubelet 在尝试访问 `https://registry.invalid` 获取镜像时因网络层解析失败而终止。K8s 控制器捕获该错误后，将容器状态标记为 `ImagePullBackOff` 并指数退避（事实 2, 3），进而导致 Pod 长期停留在 `Pending` 状态（事实 4）。Metric 数据（事实 5, 6）进一步证实了这一非应用逻辑错误的状态。

---

## 📊 性能统计

```text
├─ 总耗时: 54.4s
├─ 问题定位: 21.0s
├─ 并发证据采集: 24.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 24.2s (Evidence 18.6s, RCA 5.4s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
