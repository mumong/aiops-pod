## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... failed to resolve reference... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证明 DNS 解析失败，镜像仓库地址无效 |
| 2 | K8s Event | Kubernetes | `Error: ErrImagePull` (14m, x4) | 确认镜像拉取过程中的具体错误类型 |
| 3 | K8s Event | Kubernetes | `ImagePullBackOff` (13m, x6) 和 `BackOff` (18s, x67) | 确认 Pod 进入拉取失败后的重试退避状态 |
| 4 | K8s Config | Kubernetes | CPU: 5m/50m, Memory: 8Mi/32Mi (Container: app) | 确认资源限制极低，排除因资源不足导致启动失败 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `ImagePullBackOff`) | 监控指标层面确证 Pod 处于等待拉取镜像状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认容器尚未启动，排除了启动后崩溃的可能 |

**证据说明：**
Kubernetes 事件（#1）明确指出 `registry.invalid` 无法解析（`no such host`），这构成了根本原因。事件（#2-3）展示了从首次拉取失败到进入 BackOff 退避状态的完整时间线。监控指标（#5-6）在时间切片上交叉验证了 Pod 的“等待”状态和“零重启”事实，排除了网络短暂波动导致 Pod 启动后崩溃等其他可能性。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置了无效域名 'registry.invalid' (事实 #1) → DNS 解析失败 (no such host) → 镜像拉取失败触发重试退避 (BackOff) → Pod 处于 ImagePullBackOff 状态 (事实 #3, #5)
```

### 根因结论

已确认根因为 Pod 配置的镜像仓库域名 `registry.invalid` 无效，导致容器运行时在进行 DNS 查询时失败（`lookup registry.invalid on 127.0.0.53:53: no such host`），从而引发镜像拉取失败。

该结论得到以下事实支撑：
- 原始报错明确指出域名解析失败（证据 #1）。
- 事件记录显示了完整的拉取失败到退避的重试过程（证据 #2, #3）。
- 监控数据证实 Pod 处于 Waiting 状态且无重启记录（证据 #5, #6），符合镜像不可达的典型表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.5s
├─ 并发证据采集: 63.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 63.0s (Evidence 54.3s, RCA 8.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
