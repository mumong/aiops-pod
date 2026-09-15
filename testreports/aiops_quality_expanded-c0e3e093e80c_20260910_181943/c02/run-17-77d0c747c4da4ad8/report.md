## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet | `container.waiting_reason`: "ImagePullBackOff", `container.waiting_message`: "Back-off pulling image..." | 确认容器最终状态，证实拉取失败已进入退避期 |
| 2 | K8s Event | kubelet | "Failed to pull image \"registry.invalid/aiops/workload:missing\": rpc error: ... failed to do request: Head \"https://registry.invalid/v2/...\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host" | 提供失败直接原因：DNS 无法解析镜像仓库域名 |
| 3 | K8s Event | kubelet | "Error: ErrImagePull" (x4), "Error: ImagePullBackOff" (x6) | 记录故障演进过程：从首次拉取失败到退避 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason="ImagePullBackOff"): 1 | 独立观测印证 Pod 处于镜像拉取失败的等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 确认容器未启动过，故障为持续性而非瞬时重启问题 |

证据表明：K8s 状态与 Prometheus 监控数据高度一致，均指向 `ImagePullBackOff`；K8s 事件日志提供了决定性证据，明确指出 DNS 查询 `registry.invalid` 失败（`no such host`）是导致拉取失败的根本原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了无效的镜像域名 "registry.invalid" → 集群 DNS (127.0.0.53) 解析域名失败 → kubelet 无法建立连接拉取镜像 → 容器进入 ImagePullBackOff 状态且无法启动
```

### 根因结论

已确认根因为 **Pod 配置了无效的镜像仓库域名 `registry.invalid`**（引用证据 #2）。

该域名在集群网络中不可解析，导致 kubelet 在尝试通过 `https://registry.invalid/v2` 拉取镜像 `missing` 时，因 `lookup ... no such host` 错误而拉取失败。由于镜像拉取失败，Pod 进入 `ImagePullBackOff` 状态，无法提供业务服务。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.3s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 35.6s (Evidence 29.0s, RCA 6.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
