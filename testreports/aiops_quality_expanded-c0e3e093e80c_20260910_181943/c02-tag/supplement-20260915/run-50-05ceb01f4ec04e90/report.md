## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 指定镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在远程仓库中不存在 (Tag Missing) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态: `Pending` | 确认故障持续且 Pod 尚未就绪 |
| 2 | K8s Config | kubernetes | 容器限制: Memory `32Mi`, CPU `50m` | 排除因资源限制导致容器启动失败的可能 |
| 3 | K8s Event | kubernetes | `Error: ErrImagePull`, `Error: ImagePullBackOff` | 直接描述镜像拉取失败的状态机制 |
| 4 | K8s Event | kubernetes | `Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 精确指出未找到的完整镜像地址 |
| 5 | K8s Event | kubernetes | `not found`: `failed to resolve reference "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 确认远程仓库返回 404/NotFound 错误 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason[reason="ImagePullBackOff"]` 值为 `1` | 独立观测确认镜像拉取阻塞原因 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 确认容器未成功运行过，排除重启后的状态 |

**证据印证与说明：**
Kubernetes Event (事实 4, 5) 提供了决定性的仓库错误原文（NotFound），结合 K8s State (事实 1) 的 Pending 状态与 Metric (事实 6) 的 ImagePullBackOff 等待原因，形成闭环。资源限制配置（事实 2）与重启次数为 0（事实 7）进一步排除了 OOM 或资源争用导致启动失败的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
远程仓库中镜像 tag 不存在 (Tag Missing) → 镜像拉取失败 (ErrImagePull) → Kubelet 拉取重试并进入等待 (ImagePullBackOff) → Pod 状态变为 Pending (未就绪)
```

### 根因结论

已确认的根因为：指定镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在（Tag Missing）。

该根因由以下事实直接支持：
1.  **Kubernetes Event (事实 4, 5)** 明确记录了 `rpc error: code = NotFound` 及 `not found` 的仓库解析失败信息，精确匹配配置的镜像名称。
2.  **Kubernetes Event (事实 3)** 与 **Metric (事实 6)** 分别从事件日志和监控指标层面证实了故障表现为 `ImagePullBackOff`，而非 OOMKilled 或其他资源异常。
3.  **资源与启动状态 (事实 1, 2, 7)** 确认了容器从未成功启动，排除了镜像拉取成功但启动失败（如配置错误）的次要可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.2s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-v07/workload: 43.9s (Evidence 37.5s, RCA 6.2s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
