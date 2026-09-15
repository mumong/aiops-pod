## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ErrImagePull | Pod 配置中使用了无效的镜像域名 registry.invalid，导致 kubelet 无法解析域名并拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-65b7f54794-z7kdp` 状态为 `Pending`；容器 `app` 重启次数为 0 | 确认故障发生在启动初期，Pod 始终未进入运行状态 |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存请求 `8Mi`，上限 `32Mi`；CPU 请求 `5m`，上限 `50m` | 排除资源调度或资源耗尽导致的故障因素 |
| 3 | K8s Event | Kubernetes | `Warning  Failed  ... Error: ErrImagePull`（fact-1595db8f0c0c） | 直接指示镜像拉取阶段失败 |
| 4 | K8s Event | Kubernetes | `Warning  Failed  ... Failed to pull image... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`（fact-ad86efbd71f6） | 提供根本原因：DNS 解析失败，域名 `registry.invalid` 不存在 |
| 5 | K8s Event | Kubernetes | `Normal   BackOff  ... Back-off pulling image "registry.invalid/aiops/workload:missing"`（fact-3d6d6e4df63c） | 证实 kubelet 尝试拉取的镜像路径包含无效域名 |
| 6 | K8s Event | Kubernetes | `Warning  Failed  ... Error: ImagePullBackOff`（fact-d56e9cdc1f29） | 证实拉取失败后的持续重试与退避行为 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 显示 `ImagePullBackOff` 值为 1（fact-2f34591acad2） | 从监控层面验证了等待原因，与 K8s Event 结果一致 |

**证据说明：**
*   K8s 事件（#3-6）完整记录了从“拉取失败（ErrImagePull）”到“DNS 解析报错（no such host）”再到“退避重试（BackOff）”的时间线，直接锁定了故障点在镜像拉取环节。
*   Metric（#7）独立证实了 Pod 处于 `ImagePullBackOff` 状态，与事件日志完全印证。
*   容器配置（#2）表明资源设置极低（内存 8Mi/32Mi），非内存溢出（OOM）导致；重启数为 0 排除了启动后崩溃的可能性。

## 🎯 根因分析 · g1

```text
Pod 配置了无效的镜像域名 (registry.invalid) → 镜像拉取请求发出 (DNS Lookup) → DNS 解析失败 (no such host) → Pod 卡在 Pending 状态 (ErrImagePull/ImagePullBackOff)
```

### 根因结论

已确认的根因为 **Pod 镜像配置错误**。

*   **具体原因**：Pod 配置中的镜像地址 `registry.invalid/aiops/workload:missing` 使用了无效的域名 `registry.invalid`。
*   **造成现象的机制**：kubelet 尝试解析该域名以连接镜像仓库进行拉取时，通过 DNS（127.0.0.53:53）查询失败（错误原文：`no such host`），导致拉取动作无法发起，进而触发 `ErrImagePull` 和 `ImagePullBackOff` 状态（见证据 #3, #4, #6）。
*   **支撑证据**：K8s 事件 `fact-ad86efbd71f6` 提供了明确的 DNS 解析失败原文；Metric `fact-2f34591acad2` 确认了最终的等待原因。
*   **排查排除**：容器重启次数为 0 且 Pod 处于 Pending 状态，证明 Pod 尚未启动，排除了业务逻辑或容器内应用导致的故障。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 22.9s
├─ 并发证据采集: 541.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 541.2s (Evidence 537.2s, RCA 3.9s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
