## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 持续处于 ImagePullBackOff/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: ImagePullBackOff` (持续 58m) | 明确 Pod 当前异常状态为镜像拉取退避中 |
| 2 | K8s Event | kubernetes | `Error: ErrImagePull` -> `failed to pull and unpack image ... dial tcp: lookup registry.invalid ... no such host` | 揭示拉取失败的底层原因：DNS 解析域名 `registry.invalid` 失败 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ErrImagePull"} = 1` | 验证容器处于等待拉取镜像的阶段，支持 K8s 事件结论 |
| 4 | K8s State | kubernetes | `Pod status = Pending` | 确认 Pod 未能完成启动流程，与镜像拉取失败一致 |

**证据印证：**
K8s Event 提供了确切的错误链（ErrImagePull 至 DNS 失败）与时间跨度（58m），Metric 数据证实了该等待状态在监控窗口内持续存在。两者共同将问题锁定在镜像拉取阶段，排除了运行时错误的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像仓库域名 registry.invalid 无效/不可达 → kubelet DNS 解析失败 (no such host) → 镜像拉取失败 (ErrImagePull) → Pod 进入 ImagePullBackOff/Pending 状态
```

### 根因结论

已确认根因为 **Pod 配置了无效或不可达的镜像仓库域名 `registry.invalid`**。
该配置导致 kubelet 在尝试拉取镜像时遭遇 DNS 解析失败（`no such host`），直接引发镜像拉取错误。证据显示此错误已持续 58 分钟，期间 Pod 处于 Pending 状态且处于退避重试中 [证据 #1, #2, #4]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.0s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 39.5s (Evidence 32.3s, RCA 7.1s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
