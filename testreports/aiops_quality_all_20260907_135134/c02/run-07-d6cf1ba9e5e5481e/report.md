## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes (pod.status) | status: `Pending` | 确认 Pod 未启动 |
| 2 | K8s Event | Kubernetes (event.message) | `Error: ErrImagePull` | 镜像拉取失败触发 |
| 3 | K8s Event | Kubernetes (event.message) | `Error: ImagePullBackOff` | 失败后重试退避触发 |
| 4 | K8s Event | Kubernetes (event.message) | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证据：解析域名失败 |
| 5 | Metric | Prometheus (reason) | `ImagePullBackOff` (value: `1`) | 确认异常持续状态 |
| 6 | Metric | Prometheus (phase) | `Pending` (value: `1`) | 确认 Pod 阶段 |

Kubernetes 事件事实 4 明确指出了 `no such host` 错误，直接证实了 `ImagePullBackOff` (事实 3) 的根本原因是域名解析失败，且 Metric 数据 (事实 5, 6) 在状态上与此完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid 无效或 DNS 不可达 → kubelet DNS 解析失败 (no such host) → 镜像拉取失败触发 ErrImagePull → Pod 处于 Pending 状态且容器未启动
```

### 根因结论

已确认根因为：**镜像地址 `registry.invalid/aiops/workload:missing` 中的域名 `registry.invalid` 不可达，导致 kubelet 无法解析 DNS 并拉取镜像**。

该结论由 Kubernetes 事件 (事实 4) 中 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` 直接证实，表明网络层或配置层无法找到该域名对应的 IP。Metric (事实 5, 6) 佐证了 Pod 因此处于 `ImagePullBackOff` 和 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 56.1s
├─ 问题定位: 13.2s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 35.3s (Evidence 27.2s, RCA 8.0s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
