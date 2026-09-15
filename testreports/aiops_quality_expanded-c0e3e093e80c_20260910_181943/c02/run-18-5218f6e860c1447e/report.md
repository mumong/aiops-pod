## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，容器 app 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ImagePullBackOff` | 确认 Pod 处于镜像拉取失败并进入指数退避的状态 |
| 2 | K8s Event | Kubernetes | `Warning Failed`: `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明核心原因是域名 `registry.invalid` 解析失败 |
| 3 | K8s State | Kubernetes | `pod.phase`: `Pending` | 确认 Pod 因无法就绪而被调度器保持在 Pending 状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (app, ImagePullBackOff): `1` | 独立观测确认等待原因为镜像拉取失败 |

**证据互证分析**：
事实 #2 提供了决定性的错误堆栈，指出 DNS 解析失败是导致镜像拉取失败的根本原因；事实 #1 和 #4 从容器状态和指标层面独立确认了 `ImagePullBackOff` 的现象。事实 #3 说明该故障导致 Pod 无法完成启动。日志与 Tracing 因容器未启动而未产生数据，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 `registry.invalid` 作为镜像地址 → DNS 解析失败 (no such host) 导致无法连接镜像仓库 → kubelet 反复拉取镜像报错并进入指数退避 → Pod 进入 ImagePullBackOff 和 Pending 状态
```

### 根因结论

已确认的根因是 Pod 配置了无效的镜像域名 `registry.invalid`。

该域名的 DNS 解析失败导致 kubelet 无法从镜像仓库拉取镜像，从而触发了 Kubernetes 的 `ImagePullBackOff` 状态。此结论由 Kubernetes 事件的错误日志（`no such host`）以及容器等待原因（`ImagePullBackOff`）直接支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 12.6s
├─ 并发证据采集: 71.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 71.7s (Evidence 63.8s, RCA 7.8s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
