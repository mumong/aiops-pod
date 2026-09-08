## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 持续处于 Pending / ImagePullBackOff 状态，容器 'app' 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Normal BackOff: Back-off pulling image "registry.invalid/aiops/workload:missing" (x416 over 95m) | 直接证实镜像拉取因域名无效被 Kubelet 持续重试并指数退避 |
| 2 | K8s State | kubernetes | Pod phase: Pending, condition: ContainersNotReady, Waiting reason: ImagePullBackOff | 描述 Pod 处于 Pending 且无法启动容器的最终状态 |
| 3 | K8s Config | kubernetes | 容器 'app' 指定镜像: "registry.invalid/aiops/workload:missing" | 定位引发拉取失败的配置源头（registry.invalid 为无效域名） |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1 (single sample) | 从集群指标视角独立观测到该 Pod 正在经历的拉取失败状态 |

**证据说明：**
Kubernetes 的 Event 详细记录了镜像拉取被拒的实时动态，而 Prometheus 指标（#4）作为外部独立视图，确认了同一异常状态。配置（#3）揭示了上述失败的根本原因——配置了不可解析的 Registry 域名，这与 Event 中的报错内容完全吻合，共同构成了完整的证据链。

## 🎯 根因分析 · g1

```text
Pod Spec 配置了无效域名(registry.invalid)的镜像地址 → Registry 无法解析导致镜像拉取持续失败 → Kubelet 进入 BackOff 重试，Pod 处于 ImagePullBackOff 状态 → 应用无法启动
```

**根因结论：**
已确认根因为 Pod 的镜像配置无效。根据事实 #1 (Event) 和 #3 (Config)，Pod 被配置为从 `registry.invalid/aiops/workload:missing` 拉取镜像。由于该域名在底层网络中不可解析，Kubelet 反复尝试拉取失败并触发 `BackOff` 机制（重试次数已达 416 次），导致容器一直处于 `ImagePullBackOff` 状态（事实 #2 和 #4）。现有 K8s State 和 Metrics 证据足以支撑该结论。Logging/Tracing 因容器无法启动而缺失，但不影响对此类拉取前异常的诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 26.3s
├─ 并发证据采集: 82.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 82.8s (Evidence 69.9s, RCA 12.7s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
