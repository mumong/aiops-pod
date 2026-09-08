## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置了无效的镜像域名 registry.invalid（DNS no such host），且未配置 imagePullSecrets，导致 kubelet 无法解析并拉取镜像，进而陷入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | Pending | 描述 Pod 停滞在调度的最终状态，未进入运行阶段 |
| 2 | K8s State | container.waiting_reason | ImagePullBackOff | 确认 Pod 处于镜像拉取失败并退避重试的明确状态 |
| 3 | K8s Event | event.message | Failed to pull image... failed to resolve reference... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host | 确认根因为 DNS 解析失败，域名 registry.invalid 无效 |
| 4 | K8s Event | event.message | Back-off pulling image... | 确认集群正在执行指数级退避的拉取重试 |
| 5 | Metric | kube_pod_container_status_waiting_reason | 1 (container: app, reason: ImagePullBackOff) | 从监控侧印证 Pod 处于拉取失败的等待状态 |
| 6 | K8s State | pod.condition | Ready: False (ContainersNotReady) | 确认容器未就绪，导致 Pod 整体不可用 |

**证据关联：**
K8s 状态与事件直接指向镜像拉取机制失败，DNS 错误（证据 3）提供了精确的失败路径；Metrics（证据 5）独立验证了该状态在时序上持续存在。日志与追踪因容器未启动而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效镜像域名 registry.invalid (DNS no such host) → kubelet 无法解析并拉取镜像 → 触发 Error: ImagePullBackOff 及退避策略 → Pod 保持 Pending 状态，未 Ready
```

### 根因结论

已确认的根因为 Pod 配置了无效的镜像域名 `registry.invalid`，且未配置 `imagePullSecrets`。Kubelet 尝试拉取该镜像时遭遇 DNS 解析失败（no such host），导致镜像拉取始终失败并进入退避重试循环，最终使 Pod 处于 `Pending` 且 `ImagePullBackOff` 的状态（见证据 3、4、5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.5s
├─ 并发证据采集: 45.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 45.8s (Evidence 40.2s, RCA 5.4s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
