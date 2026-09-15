## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 持续处于 Pending 和 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed... Error: ErrImagePull` 及 `Warning Failed... Error: ImagePullBackOff` | 确认 Pod 长期处于拉取镜像失败的异常状态 |
| 2 | K8s Event | kubelet | `BackOff... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 记录重试背退行为及具体的失败镜像路径 |
| 3 | K8s Event | kubelet | `Failed to pull image... rpc error... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供决定性的根因：DNS 解析域名 `registry.invalid` 失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (container="app", reason="ImagePullBackOff") = 1 | 指标层面印证镜像拉取阻塞是容器当前等待的唯一原因 |
| 5 | K8s State | Kubernetes | `pod.status: Pending` | 确认 Pod 尚未启动，无容器运行数据 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认 Pod 尚未进入重启循环，故障处于初始化阶段 |

**证据分析**：K8s 事件（#3）中的 `lookup registry.invalid ... no such host` 直接指明了网络/配置层面的阻断点。Metric 数据（#4, #6）与 K8s 状态（#5, #1）相互印证，排除了资源不足或应用崩溃导致的重启问题，确认故障完全停留在镜像拉取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置了无效域名 registry.invalid → DNS 解析失败 (no such host) → 镜像拉取请求被阻断 (ErrImagePull) → Pod 处于 ImagePullBackOff 状态
```

### 根因结论

**已确认的根因**：容器镜像仓库地址配置错误。

Pod `aiops-case-02/workload-65b7f54794-z7kdp` 无法启动的原因是 kubelet 尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时，DNS 无法解析域名 `registry.invalid`（见证据 #3）。这导致镜像拉取流程在连接建立前即告失败，进而引发 `ImagePullBackOff` 状态。现有 K8s 事件与 Metric 事实形成了完整的证据链，足以确认该配置错误为直接根因。

---

## 📊 性能统计

```text
├─ 总耗时: 57.9s
├─ 问题定位: 17.7s
├─ 并发证据采集: 31.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 31.5s (Evidence 23.9s, RCA 7.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
