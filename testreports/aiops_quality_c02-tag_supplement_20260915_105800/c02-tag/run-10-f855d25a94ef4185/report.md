## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod配置的镜像标签 'aiops-fixture-unavailable-20260908' 在远程镜像仓库中不存在（返回 NotFound），导致Kubernetes无法拉取镜像并启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | diagnosis | 状态为 `ImagePullBackOff`，现象明确描述镜像标签 'aiops-fixture-unavailable-20260908' 在远程镜像仓库中不存在（返回 NotFound） | 直接证实了 Pod 启动失败的根本原因：镜像拉取资源缺失 |
| 2 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 1（labels: container=app, reason=ImagePullBackOff） | 指标数据确认了应用容器处于因镜像拉取失败等待的状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 | 排除了因容器运行中崩溃反复重启导致状态异常的可能，确认为启动即失败 |

现有证据高度一致，Kubernetes 诊断状态与 Prometheus 监控指标相互印证，共同指向镜像不可用这一单一事实。

## 🎯 根因分析 · g1

### 因果链

```text
远程镜像仓库中 'aiops-fixture-unavailable-20260908' 镜像标签不存在（NotFound） → Kubernetes 无法拉取容器镜像 → 容器启动失败（Exit Code/Waiting） → Pod 呈现 ImagePullBackOff 状态
```

### 根因结论

- 已确认根因：Pod 配置的镜像标签 `aiops-fixture-unavailable-20260908` 在远程镜像仓库中不存在（证据 #1、#2）。该缺失导致 Kubernetes 无法完成镜像拉取，从而使 Pod 持续处于 `ImagePullBackOff` 状态。
- 已知未知项：无法从现有数据中区分该镜像标签是被意外删除还是从未存在；也无法确认 Pod 当前配置是否为预期的正确版本，需人工介入核实部署配置。

---

## 📊 性能统计

```text
├─ 总耗时: 52.1s
├─ 问题定位: 17.3s
├─ 并发证据采集: 28.5s
│  └─ g1 aiops-case-v07/workload: 28.5s (Evidence 23.0s, RCA 5.3s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
