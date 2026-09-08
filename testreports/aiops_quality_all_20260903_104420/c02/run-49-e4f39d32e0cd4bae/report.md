## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器 app 等待启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (发生416次) | 直接证明容器镜像拉取失败及重试退避过程 |
| 2 | K8s State | Pod Status | 状态为 `Pending`，容器重启次数 `0` | 证实 Pod 处于未启动阶段，尚未产生运行时指标 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 独立确认了容器等待原因为镜像拉取失败 |
| 4 | K8s Config | 资源配置 | `memory.request: 8Mi`, `memory.limit: 32Mi` | 提供运行环境上下文，排除因资源限制导致的启动失败 |

Kubernetes 事件与 Prometheus 指标在“等待原因”上完全一致，均指向镜像拉取失败。Pod 重启数为 0 且状态为 Pending，印证了镜像根本无法被获取，因此容器未进入运行态，日志和 Trace 数据缺失（状态为 not_applicable）是物理层面的必然结果，而非数据丢失。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置了无效域名镜像地址 (registry.invalid/aiops/workload:missing) → Kubelet 无法解析并连接镜像仓库拉取镜像 → 拉取失败并进入 BackOff 状态 → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因是 Pod 配置了无效的容器镜像仓库域名 (`registry.invalid`)。
- 证据 [1] 显示 Kubelet 持续报出 `Back-off pulling image "registry.invalid/aiops/workload:missing"`，表明镜像地址不可达。
- 证据 [3] 中的 Metric `ImagePullBackOff` 独立验证了该状态。
- 由于容器始终未能启动，系统未生成业务日志（日志维度标记为 `not_applicable`），因此根因锁定在镜像配置本身。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 34.1s
├─ 并发证据采集: 38.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 38.6s (Evidence 30.5s, RCA 8.0s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
