## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认网络层无法解析镜像域名，是导致拉取失败的直接原因 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `ImagePullBackOff` | 描述 Pod 当前等待状态的最终结果 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"}` 值为 `1` | 独立于 K8s 事件的状态快照，印证 ImagePullBackOff 状态的确立 |
| 4 | Logging | kubectl_logs | `container "app" in pod "workload-65b7f54794-rnlv4" is waiting to start: trying and failing to pull image` | 补充说明容器未进入运行态，排除了应用层日志缺失的可能性 |

**证据分析：**
Kubernetes 事件记录明确指出了 `no such host` 这一核心错误，而 Metrics 指标确认了这一状态在监控维度同样被捕获；K8s 事件与 Metric 相互印证，共同锁定了“DNS 解析失败导致镜像拉取阻断”这一事实，逻辑链条完整。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置无效镜像域名 (registry.invalid) → 集群 DNS (127.0.0.53) 解析失败 → 镜像拉取终止 (no such host / ImagePullBackOff)
```

### 根因结论

已确认根因为**镜像域名配置无效导致 DNS 解析失败**。

证据（编号 1、2、3）显示 `registry.invalid` 是一个不可达或未被 DNS 记录的域名，致使 `kubelet` 在尝试拉取镜像时遭遇底层网络 DNS 查询失败（`dial tcp: lookup registry.invalid ... no such host`），进而触发了 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.9s
├─ 并发证据采集: 49.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 49.4s (Evidence 41.4s, RCA 7.9s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
