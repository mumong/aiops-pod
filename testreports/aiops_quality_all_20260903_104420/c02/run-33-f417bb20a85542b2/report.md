## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: ImagePullBackOff | 明确指示当前异常状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: Back-off pulling image "registry.invalid/aiops/workload:missing" | 直接显示导致异常的具体镜像引用 |
| 3 | K8s Event | Kubernetes | Back-off pulling image "registry.invalid/aiops/workload:missing" (x284 over 68m) | 确认拉取失败现象已持续约 68 分钟且处于指数退避状态 |
| 4 | K8s Config | Kubernetes | `container.resource_request.cpu`: 5m, `memory`: 8Mi, `resource_limit.memory`: 32Mi | 提供资源分配上下文，确认非资源调度或限制问题 |
| 5 | K8s State | Kubernetes | Pod Status: Pending, Ready: False, RestartCount: 0 | 确认容器尚未启动，无重启记录 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (ImagePullBackOff): 1 | 从监控指标层面印证当前处于等待拉取状态 |

证据显示：Kubernetes 状态与事件均指向同一镜像 `registry.invalid/aiops/workload:missing` 的拉取失败，且持续时间长（68m）并伴有严重的重试退避（x284）；Metrics 确认该等待状态持续存在；资源配置极低（5m CPU/8Mi Mem）排除资源限制导致的调度或启动异常。

## 🎯 根因分析 · g1

### 因果链
```text
容器镜像配置了 RFC 2606 保留域名 registry.invalid → kubelet 解析/连接镜像仓库失败 → ImagePullBackOff 重试退避 (Back-off pulling image) → Pod 持续 Pending 且未就绪
```

### 根因结论
**已确认的根因**：Pod 配置的容器镜像 `registry.invalid/aiops/workload:missing` 使用了 RFC 2606 保留的无效域名 `registry.invalid`，导致 kubelet 在尝试解析并连接该镜像仓库时发生 DNS 解析或连接失败，进而触发 Kubernetes 的 `ImagePullBackOff` 重试退避机制。

**证据支撑**：
1. 容器等待状态和消息直接指出了具体的失败镜像地址 `registry.invalid/aiops/workload:missing`（证据 #1, #2）。
2. K8s Event 记录证实了长达 68 分钟、近 284 次的拉取退避重试记录（证据 #3）。
3. Metric 数据印证了当前状态确为 ImagePullBackOff（证据 #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.0s
├─ 并发证据采集: 58.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 58.0s (Evidence 48.8s, RCA 9.0s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
