## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置的容器镜像 registry 地址 'registry.invalid' 无效，导致 kubelet 解析域名失败（DNS no such host），无法拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-1937c0ce6af4` Normal BackOff Back-off pulling image "registry.invalid/aiops/workload:missing" | 确认镜像拉取被退避重试 |
| 2 | K8s Event | kubernetes | `fact-ed661ffe76ba` Warning Failed Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host | 直接证据：DNS 解析失败导致镜像拉取终止 |
| 3 | Metric | prometheus | `fact-09053aab9804` kube_pod_container_status_waiting_reason=1 (container: app, reason: ImagePullBackOff) | 确认容器处于等待状态，原因明确为镜像拉取问题 |

上述证据链完整：Metric 确认 `ImagePullBackOff` 状态，K8s 事件记录从 BackOff 到最终 DNS `no such host` 的失败详情，直接定位到镜像地址 `registry.invalid` 配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置无效 registry 地址 'registry.invalid' → kubelet 解析域名失败 (DNS no such host) → 镜像拉取中断并进入 BackOff 状态 → Pod 持续处于 Pending/ImagePullBackOff 状态
```

### 根因结论

**已确认根因**：Pod 容器镜像地址配置错误（`registry.invalid`）。
证据编号 `fact-ed661ffe76ba` 明确记录 kubelet 尝试拉取镜像时发生 DNS 解析失败（`no such host`），结合 `fact-1937c0ce6af4` 和 Metric 的 `fact-09053aab9804` 确认该错误直接导致镜像无法拉取，从而产生 `ImagePullBackOff` 现象。

---

## 📊 性能统计

```text
├─ 总耗时: 42.8s
├─ 问题定位: 16.0s
├─ 并发证据采集: 19.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 19.7s (Evidence 15.3s, RCA 4.2s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
