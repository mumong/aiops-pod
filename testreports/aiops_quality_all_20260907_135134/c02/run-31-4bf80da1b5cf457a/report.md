## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning  Failed          33m (x4 over 34m)      kubelet            Error: ErrImagePull` (fact-2233e7d88db7) | 确认底层报错为镜像拉取失败 |
| 2 | K8s Event | kubernetes | `Warning  Failed          33m (x4 over 34m)      kubelet            Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-3ecf619f3e75) | 根因证据：明确指明无法解析 `registry.invalid` 域名 |
| 3 | K8s State | kubernetes | `{"container": "app", "reason": "ImagePullBackOff"}` (fact-bb1f16efc7da) | 确证异常状态 |
| 4 | K8s State | kubernetes | `{"container": "app", "message": "Back-off pulling image \"registry.invalid/aiops/workload:missing\""}` (fact-0328eb4e7846) | 确认正在尝试拉取的具体无效镜像引用 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"}` 值为 1 (fact-9f854cb8c2df) | 指标层面验证了处于 ImagePullBackOff 状态的事实 |

**证据分析：**
Kubernetes 事件直接给出了 DNS 解析失败的错误信息，Metric 指标状态与 K8s 状态完全一致。日志和追踪为空符合 Pod 无法启动的物理限制。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid 无法进行 DNS 解析 (no such host) → kubelet 拉取镜像时因域名解析失败报错 → 镜像拉取失败并进入退避重试 (ImagePullBackOff) → Pod 容器一直处于 Pending 状态，应用不可用
```

### 根因结论

已确认的根因为 Pod 配置的镜像仓库域名 `registry.invalid` 无效且 DNS 不可达。

**证据支撑：**
K8s 事件（证据 2）明确记录了 `lookup registry.invalid on 127.0.0.53:53: no such host` 错误，直接证实了镜像拉取失败的根源；K8s 状态（证据 3）及 Metric（证据 5）均确认该异常持续存在。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.1s
├─ 并发证据采集: 36.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 36.9s (Evidence 29.9s, RCA 6.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
