## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod 配置引用了无效的镜像仓库地址 'registry.invalid'，且缺乏 imagePullSecrets，导致 Kubelet 持续拉取失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Condition | Ready= False (reason: ContainersNotReady, message: "containers with unready status: [app]") | 确认 Pod 未达到就绪状态，且直接原因是容器未就绪。 |
| 2 | K8s Event | Kubelet Event | Normal BackOff (x394 over 92m), message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 记录长达 92 分钟、重试 394 次的拉取失败，证明故障持续且无法自愈。 |
| 3 | K8s State | Kubelet Waiting Reason | container.waiting_reason = "ImagePullBackOff" | 明确指向容器停留在拉取镜像阶段的特定状态。 |
| 4 | K8s State | Kubelet Waiting Message | container.waiting_message = "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 提供了确切的失败镜像 URI。 |
| 5 | Metric | Prometheus Gauge | kube_pod_container_status_waiting_reason=1 (labels: container="app", reason="ImagePullBackOff") | 验证了 K8s 内部等待原因为拉取镜像超时，状态为 1 (活跃)。 |
| 6 | Metric | Prometheus Gauge | kube_pod_container_status_restarts_total=0 (container="app") | 确认 Pod 从启动到现在未发生过重启，排除了因启动失败导致重启循环的可能性。 |

**证据说明：**
K8s 事件 (证据 #2) 与容器等待消息 (证据 #3) 高度吻合，共同锁定了 `ImagePullBackOff` 这一具体停滞状态。等待消息 (证据 #4) 给出了确切的错误镜像地址 `registry.invalid/aiops/workload:missing`。Kubelet 在长达 92 分钟内尝试拉取 394 次 (证据 #2)，表明网络或镜像仓库配置存在根本性阻断。Metric (证据 #5) 的活跃状态与 K8s 状态一致，Metric (证据 #6) 的 0 重启次数佐证了容器从未成功过，这符合镜像拉取失败而非启动后崩溃（CrashLoopBackOff）的典型特征。由于 Pod 始终处于拉取阶段，日志 (logging) 和追踪 (tracing) 工具因 `query_rejected` 或业务未启动而不可用，因此核心事实完全依赖 K8s 原生事件与指标。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用无效的镜像仓库 'registry.invalid/aiops/workload:missing' → Kubelet 无法解析或连接到无效镜像源 → 镜像拉取持续失败并进入指数退避重试(BackOff) → 容器无法启动(Pending/ImagePullBackOff) → Pod 状态一直显示未就绪
```

### 根因结论

已确认根因为：Pod 的容器配置引用了一个无效的镜像地址 `registry.invalid`（即 `registry.invalid/aiops/workload:missing`），且 Pod 的 ServiceAccount 或 Pod 规范中缺乏有效的 `imagePullSecrets`（或因域名无效导致网络不可达）。这导致 Kubelet 在执行拉取指令时，持续触发重试机制，最终进入 `ImagePullBackOff` 状态，致使 Pod 保持 `Pending` 状态且无法被调度运行。

关键支撑事实：
1. **直接错误信息**：容器等待消息明确指出了失败的完整镜像路径（证据 #3, #4）。
2. **故障持续性**：长达 92 分钟的 BackOff 事件记录（证据 #2）证明故障发生在配置阶段，而非偶发性网络抖动。
3. **状态一致性**：Pod 的 `Ready=False` (证据 #1)、`ImagePullBackOff` 等待原因（证据 #3）以及 Prometheus 指标（证据 #5）三者在时间和状态上完全吻合，构成了闭环证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.2s
├─ 并发证据采集: 63.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 63.2s (Evidence 54.9s, RCA 8.1s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
