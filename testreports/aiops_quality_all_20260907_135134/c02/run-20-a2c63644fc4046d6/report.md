## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置了无效的镜像仓库域名 'registry.invalid'，导致 kubelet 在执行镜像拉取时发生 DNS 解析失败（no such host），进而持续触发 ImagePullBackOff 异常。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-8060e9e783ec` | Failed to pull image: `no such host` (lookup `registry.invalid` on `127.0.0.53:53`) | 核心失败机制：DNS 解析失败，证实镜像域名无效 |
| 2 | K8s Event | `fact-48c260fbdf23` / `fact-67a3cd42a2eb` | `ErrImagePull` (x4); `ImagePullBackOff` (x6) | 关键错误信息：确认拉取失败及退避行为 |
| 3 | K8s State | `fact-51975f1c8b89` | `container.waiting_reason`: `ImagePullBackOff` | 异常状态：容器未启动的原因确认 |
| 4 | Metric | `fact-2a8b0bbdb92e` | `kube_pod_container_status_waiting_reason`: `1` (reason=`ImagePullBackOff`) | 独立验证：Prometheus 数据确认容器处于等待拉取镜像状态 |

**证据综合说明**：K8s Event 提供了镜像拉取失败的具体网络原因（DNS 解析失败）及重试退避状态（`ImagePullBackOff`），而 Prometheus 指标独立证实了该容器当前仍处于等待拉取镜像的状态，两者完全印证 Pod 因镜像域名错误无法启动。由于容器始终未运行，Logging 和 Tracing 维度无应用日志或 Trace，符合物理逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效的镜像仓库域名 (registry.invalid) → DNS 解析失败 (no such host) → 镜像拉取失败 (ErrImagePull) → 持续触发退避重试 (ImagePullBackOff) → Pod 处于 Pending 且不可用
```

### 根因结论

**已确认根因**：Pod 配置了无效的镜像仓库域名 `registry.invalid`。

该域名在 DNS 解析（指向 `127.0.0.53:53`）时直接返回 `no such host` 错误，导致 kubelet 无法拉取镜像 `registry.invalid/aiops/workload:missing`。这直接触发了 `ImagePullBackOff` 状态，使得容器无法启动。相关事实支持包括：
- 明确的 DNS 解析失败事件 (`fact-8060e9e783ec`)；
- 容器持续处于 `ImagePullBackOff` 状态 (`fact-51975f1c8b89`)；
- 等待原因的监控指标确认 (`fact-2a8b0bbdb92e`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.6s
├─ 并发证据采集: 41.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 41.8s (Evidence 37.0s, RCA 4.7s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
