## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod 的容器配置了无效镜像仓库域名 registry.invalid，导致 DNS 解析失败 (no such host) 从而引发 ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending`, `pod.phase: Pending` | 确认 Pod 处于调度完成但容器未启动状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ImagePullBackOff`, `container.waiting_message: Back-off pulling image "registry.invalid/aiops/workload:missing"` | 直接描述容器拉取镜像失败的当前状态与重试退避行为 |
| 3 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供根本原因证据：DNS 解析失败导致无法连接镜像仓库 |
| 4 | K8s Event | kubernetes | `Error: ErrImagePull` (4 次事件记录) | 确认 kubelet 持续尝试拉取镜像但失败 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (label: `reason: ImagePullBackOff`) | 独立指标确认容器处于 ImagePullBackOff 等待状态 |
| 6 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi`, `container.resource_request.cpu: 5m`, `container.resource_limit.memory: 32Mi`, `container.resource_limit.cpu: 50m` | 资源请求与限制配置，排除因资源不足导致的启动失败 |

**证据说明：**
1. **维度印证**：Kubernetes 事件（#3）与 K8s 状态（#2）在时间上和逻辑上完全一致，均指向 `registry.invalid` 域名无法解析。Prometheus 指标（#5）独立验证了该状态的存在。
2. **现象锁定**：Pod 处于 `Pending` 阶段（#1），结合 `ImagePullBackOff` 状态（#2），说明 Pod 调度正常，但容器运行时环境初始化因镜像拉取失败而阻塞。
3. **排除资源因素**：资源请求与限制配置（#6）明确存在且非零，排除了因资源不足导致容器无法启动的可能。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置了无效镜像仓库域名 registry.invalid → DNS 解析失败 (no such host) → 镜像拉取持续失败 (ErrImagePull) → Pod 进入 ImagePullBackOff 状态并拒绝启动
```

### 根因结论

**已确认的根因**：Pod `aiops-case-02/workload-65b7f54794-z7kdp` 的容器配置了不可达的镜像仓库域名 `registry.invalid`，导致节点上的 kubelet 在拉取镜像 `registry.invalid/aiops/workload:missing` 时遭遇 DNS 解析失败（`no such host`）。

**证据支撑**：
- 原始 K8s 事件 `Failed to pull image` 明确报告了 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` 错误（证据 #3）。
- 容器状态长期维持在 `ImagePullBackOff`，且重试退避行为符合预期（证据 #2, #4）。
- 资源配置正常（证据 #6），进一步排除其他启动故障可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 9.6s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 40.3s (Evidence 35.1s, RCA 5.0s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- 未调用 Runbook
