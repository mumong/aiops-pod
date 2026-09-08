## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `waiting_reason: ImagePullBackOff` (Container: app) | 指示容器状态停滞的具体阶段 |
| 2 | K8s State | Kubernetes | `waiting_message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" ` | 确认具体的镜像地址及拉取退避状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 从时序数据确认当前正在发生镜像拉取失败 |
| 4 | K8s State | Kubernetes | `pod.phase: Pending` | 说明 Pod 调度完成但实际执行未启动 |
| 5 | K8s Config | Kubernetes | `container.resource_request: cpu=5m, memory=8Mi` | 排除因资源请求过高导致调度失败或 OOM |
| 6 | K8s Config | Kubernetes | `container.resource_limit: cpu=50m, memory=32Mi` | 排除因资源限制不合理导致调度失败或 OOM |

**证据说明：**
Kubernetes 状态与 Prometheus 指标均指向同一结论：Pod 处于 `Pending` 状态，且容器处于 `ImagePullBackOff` 状态。具体的镜像地址 `registry.invalid/aiops/workload:missing` 提供了关键的错误上下文，表明问题出在镜像解析或拉取阶段，而非容器启动后的运行阶段。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS 无法解析域名 registry.invalid → 容器运行时尝试拉取镜像时网络连接失败 (failed to resolve reference) → 镜像拉取失败进入重试退避阶段 (ImagePullBackOff) → Pod 状态持续为 Pending 且 app 容器处于 Waiting 状态
```

### 根因结论

已确认的根因是**容器镜像地址配置错误**。Pod 配置了无效的镜像源 `registry.invalid/aiops/workload:missing`，导致节点上的容器运行时无法解析该域名并获取镜像。

依据：
- Kubernetes 状态显示 `waiting_message` 明确指出正在退避拉取该特定镜像（证据 #1, #2）。
- Prometheus 监控确认了 `ImagePullBackOff` 状态的持续存在（证据 #3）。
- 资源配置合理（证据 #5, #6），排除了资源竞争导致的启动失败。

---

## 📊 性能统计

```text
├─ 总耗时: 52.1s
├─ 问题定位: 12.5s
├─ 并发证据采集: 31.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 31.4s (Evidence 24.5s, RCA 6.8s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
