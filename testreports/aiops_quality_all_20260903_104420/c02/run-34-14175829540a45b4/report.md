## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (记录 x284, 持续 69m) | 核心失败证据，直接指出拉取失败并进入退避循环 |
| 2 | K8s State | kubelet | `container.waiting_reason`: `ImagePullBackOff`; `message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 明确容器当前处于因镜像拉取失败导致的等待状态 |
| 3 | K8s State | kubelet | `pod.phase`: `Pending`; `pod.condition(Ready)`: `False` (`ContainersNotReady`) | 描述 Pod 因无法就绪而长期处于 Pending 阶段的系统状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (`reason`: `ImagePullBackOff`, `container`: `app`) | 通过指标独立确认当前 Pod 容器正卡在 ImagePullBackOff 状态 |
| 5 | K8s Config | kubelet | `container.resource_limit.memory`: `32Mi`; `container.resource_request.cpu`: `5m` | 资源配置极低，但在 ImagePullBackOff 阶段与 CPU 无关，属上下文背景 |

Kubernetes 事件与状态机事实互相印证，一致指向 `registry.invalid` 这一不可达域名导致的拉取失败；Metrics 独立佐证了 `ImagePullBackOff` 的持续存在，排除了瞬态故障可能。

## 🎯 根因分析 · g1

### 因果链

```text
镜像地址 registry.invalid/aiops/workload:missing 使用无效域名 → kubelet 执行拉取操作因域名无法解析或连接失败而报错 → kubelet 进入 Back-off 重试循环并累积失败事件 → Pod 容器状态维持在 Waiting/ImagePullBackOff
```

### 根因结论

已确认根因为：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 配置的镜像仓库域名 `registry.invalid` 无效，导致 kubelet 持续拉取失败。

证据编号 1 和 2 明确指出失败的镜像路径为 `registry.invalid/aiops/workload:missing`，且系统已进入指数退避（BackOff）重试阶段。证据编号 4 的 Prometheus 指标从监控维度独立确认了该状态。因此，当前故障现象由镜像配置错误直接导致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 13.0s
├─ 并发证据采集: 54.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 54.1s (Evidence 45.1s, RCA 8.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
