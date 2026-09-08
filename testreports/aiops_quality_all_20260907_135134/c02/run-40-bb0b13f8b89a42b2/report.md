## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 持续处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes (kubelet) | `Warning Failed ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证明 DNS 解析失败，无法定位镜像仓库。 |
| 2 | K8s Event | Kubernetes (kubelet) | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 证实 kubelet 正处于镜像拉取退避等待状态。 |
| 3 | K8s Event | Kubernetes (kubelet) | `Warning Failed Error: ErrImagePull` | 证实镜像拉取操作已产生明确的错误码。 |
| 4 | K8s State | Kubernetes (Pod Status) | `status: Pending` | 证实容器未进入运行状态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason=ImagePullBackOff) | 验证 Pod 正处于 ImagePullBackOff 状态（单样本，无趋势）。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 证实容器尚未成功启动过。 |

**证据印证：**
Kubernetes 事件明确指出了 DNS 解析失败的具体原因是“lookup registry.invalid ... no such host” [1]，这直接导致了 `ErrImagePull` [3] 和随后的退避行为 [2]。监控指标仅反映了最终状态 [4, 5, 6]，未提供比事件更早的线索。由于容器未能启动，Logging 和 Tracing 维度无可观测事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 registry.invalid/aiops/workload:missing → 
DNS 解析失败 (lookup no such host) → 
kubelet 镜像拉取报错 (ErrImagePull) → 
Pod 进入 ImagePullBackOff 状态
```

### 根因结论

**已确认根因：** Pod 配置的镜像地址使用了无效域名 `registry.invalid`，导致 kubelet 执行镜像拉取时发生 DNS 解析失败，进而引发 `ImagePullBackOff`。

**证据引用：** Kubernetes 事件 `fact-2f72ff94c0eb` 中记录了明确的 `no such host` 错误，证实了域名无法解析；`fact-2224d1345b22` 确认了后续的 BackOff 状态。所有证据一致指向该配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 44.7s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 30.2s (Evidence 21.5s, RCA 8.6s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
