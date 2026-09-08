## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器未就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 核心证据：明确记录 DNS 解析失败的具体原因 |
| 2 | K8s State | kubernetes | `container.waiting_message`: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 支撑证据：确认当前状态为拉取镜像后的退避等待 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: "ImagePullBackOff" | 支撑证据：确认失败原因归类为镜像拉取失败 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason=ImagePullBackOff) | 独立观测：Prometheus 监控数据与 K8s 状态一致 |

现有证据表明，Pod 处于 `ImagePullBackOff` 状态，Kubernetes Event 直接指向了 `registry.invalid` 域名的 DNS 解析失败。Metric 数据作为独立观测维度，佐证了该状态的存在，无需通过日志或 Trace 进一步验证基础连通性失败的原因。

## 🎯 根因分析 · g1

```text
集群无法解析 registry.invalid 域名 (DNS 解析失败) → kubelet 无法获取镜像 manifest (镜像拉取失败) → 连续失败触发 Back-off 机制 (重试退避) → Pod 处于 Pending 且容器状态为 ImagePullBackOff
```

### 根因结论

已确认的根因是 **镜像仓库域名 `registry.invalid` 无法被集群 DNS 解析**（证据编号 1）。集群使用的 DNS 服务器 `127.0.0.53` 返回了 `no such host` 错误，导致 kubelet 无法连接镜像仓库并拉取 `missing` 标签的镜像，进而引发容器启动失败并进入退避等待状态（证据编号 2, 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.4s
├─ 并发证据采集: 64.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 64.9s (Evidence 56.3s, RCA 8.4s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
