## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod 配置了不可解析的容器镜像地址 'registry.invalid/aiops/workload:missing'，导致 kubelet 持续拉取失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal  BackOff  3m59s (x416 over 99m)  kubelet  Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认为持续性拉取失败，频率高且持续时间极长 |
| 2 | K8s State | Kubernetes | 容器 `app` 状态 `waiting_reason`: `ImagePullBackOff` | 确认当前处于拉取失败后的退避重试状态 |
| 3 | K8s State | Kubernetes | `pod.status`: `Pending`, `pod.phase`: `Pending` | 确认可见现象为 Pod 始终无法启动进入调度后阶段 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` 值 `1` | 监控侧印证拉取等待状态正在持续发生 |
| 5 | K8s Config | Kubernetes | 容器 `app` 资源配置 `request`: `cpu=5m`, `memory=8Mi`；`limit`: `cpu=50m`, `memory=32Mi` | 排除资源超限或 OOM 导致容器启动失败的可能性 |

证据链表明：Pod 因配置了无效镜像地址 `registry.invalid` 导致无法拉取。由于容器未能启动，日志（Logging）与流量（Tracing）数据缺失属于物理必然（无运行态），且 `kubectl logs` 明确返回 `trying and failing to pull image` 错误。K8s 状态与事件一致地指向镜像拉取阻塞，Metric 与资源配置佐证了故障与资源无关，纯粹为镜像引用错误。

## 🎯 根因分析 · g1

### 因果链

```text
镜像引用 'registry.invalid' 为无效域名 → kubelet 无法解析或连接镜像仓库 → 容器启动阻塞并进入 Back-off 重试 → Pod 保持 Pending/ImagePullBackOff 状态
```

### 根因结论

已确认根因为：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 的容器 `app` 配置了不可解析或无效的容器镜像地址 `registry.invalid/aiops/workload:missing` [1][2][3]。

该错误直接导致 kubelet 拉取镜像失败，并反复进入 `ImagePullBackOff` 退避状态。由于容器进程从未成功启动，不存在应用日志或网络追踪数据。Kubernetes 的状态（`Pending`、`ImagePullBackOff`）与 Prometheus 的监控指标完全吻合，排除了资源（如内存、CPU）不足或其他底层环境因素的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.6s
├─ 并发证据采集: 66.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 66.6s (Evidence 60.5s, RCA 5.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
