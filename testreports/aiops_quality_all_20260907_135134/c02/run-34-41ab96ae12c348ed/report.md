## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置了无效或无法解析的镜像域名 registry.invalid，导致 kubelet 在拉取镜像时发生 DNS 解析失败，进而使容器处于 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-4cec5d33bed3) | 直接证据：Kubelet 尝试拉取镜像时遭遇 DNS 解析失败，确认域名无效。 |
| 2 | K8s Event | kubernetes | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-2f9c2a0c5c2f) | 状态证据：Kubelet 因拉取失败持续进入退避阶段，确认故障持续存在。 |
| 3 | K8s Event | kubernetes | `Warning Failed ImagePullBackOff` (fact-f7daa8c5a151) | 现象证据：Pod 最终状态稳定在 ImagePullBackOff。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason=ImagePullBackOff, fact-0d6756765f58) | 确认：Metric 指标在观测时点确证了容器处于镜像拉取等待状态。 |

**证据小结**：Kubernetes 事件日志与 Prometheus 指标相互印证，均指向同一容器因无法解析 `registry.invalid` 域名而持续拉取失败，处于退避等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置包含无效域名 registry.invalid → DNS 解析失败 (lookup no such host) → 镜像拉取持续失败并进入 BackOff → Pod 状态 Pending，容器状态 ImagePullBackOff
```

### 根因结论

已确认的根因为：Pod 的镜像配置使用了无效且无法解析的域名 `registry.invalid`。

这一配置错误导致 Kubelet 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时，向本地 DNS 服务器 (`127.0.0.53`) 发起查询失败（见证据 #1），进而触发了拉取重试与退避机制（见证据 #2），最终使容器稳定处于 `ImagePullBackOff` 状态（见证据 #3）。Prometheus 指标（证据 #4）进一步确认了该状态。

---

## 📊 性能统计

```text
├─ 总耗时: 59.0s
├─ 问题定位: 17.4s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 33.2s (Evidence 25.2s, RCA 8.0s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
