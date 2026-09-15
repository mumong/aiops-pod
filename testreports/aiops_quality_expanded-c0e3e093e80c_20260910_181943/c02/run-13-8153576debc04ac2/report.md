## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod 配置了无效的镜像仓库域名 `registry.invalid`（.invalid 保留TLD不可路由），导致 kubelet 无法通过集群 DNS 解析镜像地址，从而引发镜像拉取失败与 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... failed to resolve reference... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明 kubelet 尝试拉取镜像时因 DNS 解析失败 (no such host) 而彻底中断，直接揭示根因为域名不可达。 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ImagePullBackOff` / `container.waiting_message: Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认容器当前状态为等待拉取，且处于指数退避重试阶段，与上述拉取失败事实一致。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 独立监控指标确认了容器的异常等待状态，与 K8s API 观测到的状态完全吻合。 |
| 4 | K8s State | kubernetes | `pod.phase: Pending` / `pod.condition.ContainersReady: False (ContainersNotReady)` | 表明 Pod 调度成功但未能进入运行态，排除调度失败或集群网络配置错误的可能性。 |

**证据链说明**：
Metric 观测与 K8s API 状态相互印证，确认容器长期处于 `ImagePullBackOff` 状态。关键证据在于 Event 中的 DNS 解析失败报错 (`no such host`)，该事实直接锁定了问题源头为镜像地址配置的域名无效，且由于容器未能启动，排除了应用日志或 Tracing 作为诊断依据的可能性，证据链完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 registry.invalid → 集群 DNS (127.0.0.53) 返回 "no such host" → kubelet 拉取镜像请求失败 → Pod 陷入 ImagePullBackOff
```

### 根因结论

已确认根因为 **Pod 镜像地址配置错误**（使用了保留域名 `registry.invalid`）。

该根因由以下事实共同支撑：
- **直接触发因素**：K8s Event `fact-49b96dd48e74` 明确记录了 kubelet 在解析 `registry.invalid` 时遭遇 DNS 失败 (`lookup ... no such host`)，证明域名本身无法路由。
- **持续症状**：Metric 数据 `fact-7fe747c982d0` 与 K8s State `fact-1e11ef826f59` 均确认容器持续处于 `ImagePullBackOff` 状态，且退避日志 `fact-998a81e5500c` 证实拉取操作反复失败。
- **排除其他可能**：Pod 处于 Pending 状态且未触发重启（RestartCount=0），证明资源调度与主机环境正常，故障严格隔离在镜像拉取阶段。

现有 K8s 状态、事件与指标证据充分，无需补充其他维度即可确立根因。

---

## 📊 性能统计

```text
├─ 总耗时: 59.2s
├─ 问题定位: 16.3s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 32.3s (Evidence 26.0s, RCA 6.3s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed, pod-config-error
