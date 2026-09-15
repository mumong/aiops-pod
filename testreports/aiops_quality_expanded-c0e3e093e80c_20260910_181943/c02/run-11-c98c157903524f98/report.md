## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 持续处于 ImagePullBackOff 状态，无法正常启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认 kubelet 尝试拉取镜像时因 DNS 解析失败（no such host）而报错，提供直接因果线索。 |
| 2 | K8s Event | kubelet | `Error: ImagePullBackOff` / `Error: ErrImagePull` | 确认拉取失败后的容器状态已转为回退等待，符合 DNS 失败引发的异常表现。 |
| 3 | K8s Event | kubelet | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (BackOff 134次) | 确认系统处于持续的重试退避循环中，故障具有持续性。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: ImagePullBackOff) | 从指标层面确认容器处于 ImagePullBackOff 状态。 |

证据 1 明确指出了域名 `registry.invalid` 解析失败（`no such host`）是导致拉取的直接技术原因。证据 2 和 4 分别从事件记录和监控指标两个维度确认了由此引发的 `ImagePullBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 registry.invalid → 拉取镜像时 DNS 解析失败 (no such host) → 镜像拉取永久失败 (ErrImagePull) → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因是 **Pod 配置了无效的镜像仓库域名 (`registry.invalid`)**。

该配置导致 kubelet 在向 Pod 配置的 DNS (`127.0.0.53`) 发起解析请求时无法找到对应主机，触发 `no such host` 错误并导致拉取失败（见事实编号 `fact-8058978cf718`）。由于镜像根本无法拉取，容器无法启动，系统随后自动进入退避机制，表现为持续的 `ImagePullBackOff` 状态（见事实编号 `fact-8058978cf718`、`fact-9cdc65bd14d3` 及指标 `fact-e967957e346e`）。

**未知项**：为何 Deployment 配置中使用了无效的 `registry.invalid` 域名（可能是配置错误或测试用例），但这不影响对当前故障现象的直接诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 21.5s
├─ 并发证据采集: 557.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 557.2s (Evidence 548.2s, RCA 8.9s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
