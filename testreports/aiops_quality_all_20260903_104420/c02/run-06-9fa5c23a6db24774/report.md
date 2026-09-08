## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod `workload-65b7f54794-rnlv4` 配置的镜像仓库域名 `registry.invalid` 无效，导致 kubelet 在拉取镜像 `registry.invalid/aiops/workload:missing` 时遭遇 DNS 解析失败（`lookup registry.invalid ... no such host`），从而引发 `ImagePullBackOff` 异常。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod phase: `Pending`, Waiting reason: `ImagePullBackOff` | 确认 Pod 当前无法启动，异常原因为拉取镜像失败后的退避 |
| 2 | K8s Event | Kubernetes | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供直接的 DNS 解析失败证据，揭示拉取失败的精确机制 |
| 3 | K8s Config | Kubernetes | 目标镜像: `registry.invalid/aiops/workload:missing` | 关联异常事件中的错误镜像路径，确认引发 DNS 解析失败的具体对象 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 从监控层面独立印证 Pod 处于 ImagePullBackOff 状态 |

证据 1、2、4 形成闭环：K8s 事件 (证据 2) 揭示了 `registry.invalid` 存在 DNS 解析失败，导致拉取镜像 (证据 3) 的 `Failed` 动作，进而促使 Kubelet 进入 `ImagePullBackOff` 状态 (证据 1)，并被 Metrics 实时捕获 (证据 4)。

## 🎯 根因分析 · g1

### 因果链

```text
配置的镜像仓库域名 registry.invalid 无效 → DNS 解析失败 (lookup registry.invalid ... no such host) → kubelet 拉取镜像 registry.invalid/aiops/workload:missing 失败 → Pod 进入 ImagePullBackOff 状态 (Pending)
```

### 根因结论

已确认根因：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 的容器配置指向了无效的镜像仓库域名 `registry.invalid`。
该配置导致 Kubelet 在拉取镜像 `registry.invalid/aiops/workload:missing` 时，遭遇 DNS 解析失败（`no such host`），触发了镜像拉取失败及后续的 `ImagePullBackOff` 异常（见证据 1、2）。该结论由 K8s Event (证据 2)、State (证据 1) 和 Metrics (证据 4) 相互印证，事实链条完整。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.4s
├─ 并发证据采集: 77.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 77.4s (Evidence 67.4s, RCA 9.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
