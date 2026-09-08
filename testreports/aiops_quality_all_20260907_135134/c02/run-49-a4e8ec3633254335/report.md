## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | container.waiting_reason | `app` 容器的等待原因为 `ImagePullBackOff` | 确认 Pod 因镜像拉取失败而进入退避状态，是直接的故障状态证据 |
| 2 | K8s Event | kubelet | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 提供确切的失败镜像地址；`registry.invalid` 为保留无效域名，直接指向配置错误 |
| 3 | K8s State | pod.phase / condition | Pod 处于 `Pending` 阶段，且 `ContainersReady` 为 `False` | 佐证 Pod 始终无法完成初始化，与镜像拉取失败的预期现象一致 |
| 4 | Metric | kube_pod_container_status_waiting_reason | `ErrImagePull` 值为 `1` | 独立于 K8s API 的观测，确认当前存在拉取失败的实例，支持上述状态结论 |

**证据互证说明：**
K8s Event (Fact 2) 明确记录了针对 `registry.invalid` 的拉取失败及 BackOff 动作，直接解释了 K8s State (Fact 1) 中 `ImagePullBackOff` 状态的成因。Metric (Fact 4) 与 K8s 状态观测相互印证，共同确认了故障的持续存在。由于容器尚未成功启动，Logging 和 Tracing 维度无相关应用数据，属于预期的空结果。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置 'registry.invalid/aiops/workload:missing' 使用无效保留域名 → 节点 kubelet 尝试拉取时遭遇 DNS 解析失败 → 镜像拉取持续失败触发 BackOff 机制 → Pod 持续处于 ImagePullBackOff/Pending 状态，无法启动
```

### 根因结论

已确认的根因为 **Pod 配置了使用无效域名的容器镜像**。

具体表现为 Pod 配置的镜像地址 `registry.invalid/aiops/workload:missing` 使用了保留域名 `registry.invalid`（Fact 2），该域名在公网中无法解析，导致 kubelet 无法拉取镜像。这一配置错误直接触发了 K8s 的拉取退避机制（Fact 1），致使 Pod 长期处于 `ImagePullBackOff` 和 `Pending` 状态（Fact 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.8s
├─ 并发证据采集: 53.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 53.8s (Evidence 44.3s, RCA 9.4s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
