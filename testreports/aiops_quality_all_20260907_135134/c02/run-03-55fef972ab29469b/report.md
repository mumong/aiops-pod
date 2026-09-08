## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv (aiops-case-02) 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-3a9671316346) | 确认 kubelet 尝试访问 `registry.invalid` 时，因 DNS 解析失败导致无法拉取镜像 |
| 2 | K8s Config | kubernetes | `image: registry.invalid/aiops/workload:missing` (fact-ad65c3da77c1, fact-ce8a43c9a76c) | 确认容器 Spec 中配置的镜像仓库域名无效，引发拉取失败的直接原因 |
| 3 | K8s State | kubernetes | `Waiting: { reason: "ImagePullBackOff", message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" }` (fact-5f6e38a68310) | 展示 Pod 当前处于因拉取失败而退避等待的最终状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-431da6665ccd) | 从监控维度证实了 `ImagePullBackOff` 状态的客观存在（单样本，仅确认当前状态） |

**证据综合说明：**
Kubernetes 事件直接记录了拉取 `registry.invalid` 镜像时的 DNS 解析失败错误（`no such host`），结合配置事实确认了该域名的无效性。这些证据直接导致容器状态变为 `ImagePullBackOff`，Metric 数据证实了该等待状态的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 spec 配置了无效域名 registry.invalid (fact-ce8a43c9a76c) 
→ 集群 DNS (127.0.0.53) 解析失败返回 no such host (fact-3a9671316346) 
→ kubelet 无法拉取镜像，状态转为 ImagePullBackOff (fact-5f6e38a68310) 
→ Pod 处于 Pending 状态 (fact-18e87241ba8e)
```

### 根因结论

**已确认的根因：**
Pod `workload-65b7f54794-nqrzv` 的容器配置中使用了无效的镜像仓库域名 `registry.invalid`。

该域名无法被集群 DNS (`127.0.0.53`) 解析，导致 kubelet 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时遭遇网络请求失败（`dial tcp: lookup ... no such host`）。由于镜像无法拉取，容器持续处于 `ImagePullBackOff` 状态，进而导致 Pod 无法启动并维持在 `Pending` 状态。该因果链已由 K8s 事件（fact-3a9671316346）、镜像配置（fact-ce8a43c9a76c）及等待状态事实（fact-5f6e38a68310）完整闭环证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.8s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 38.2s (Evidence 30.0s, RCA 8.1s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
