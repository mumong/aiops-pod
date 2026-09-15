## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态：Pending；`container.waiting_reason`="ImagePullBackOff"，`waiting_message`="Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 确认异常现象及阻塞原因 |
| 2 | K8s State | Kubernetes | Pod Phase：Pending；Container `app` 未就绪 (`ContainersNotReady`) | 确认容器未进入运行态 |
| 3 | K8s Config | Kubernetes | Pod 配置：`resource_request` (8Mi/5m)，`resource_limit` (32Mi/50m) | 资源请求与限制配置合理，非资源瓶颈 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`="1" (reason="ImagePullBackOff", sample_count=1) | 确认容器持续处于 ImagePullBackOff 状态 |

当前日志与追踪系统显示 `not_applicable`（限制：容器未启动，物理上不会产生应用日志或业务 Trace），且 Metric 仅存在单样本，无趋势可评估。现有证据一致指向镜像拉取失败，且 K8s 状态提供了确切的域名与状态码。

## 🎯 根因分析 · g1

### 因果链
```text
镜像仓库域名无效 (registry.invalid) → 集群 DNS 解析失败 → Kubelet 拉取镜像请求网络不可达 → Pod 状态转为 ImagePullBackOff
```

### 根因结论
已确认根因：Pod 配置使用了无效的私有镜像仓库域名 `'registry.invalid'`。
- **证据支撑**：K8s 状态显示 `waiting_message` 明确包含 `"Back-off pulling image \"registry.invalid/aiops/workload:missing\""`，且 `container.waiting_reason` 为 `ImagePullBackOff`；Metric 数据 `fact-b89551fdaa9f` 同样确认了 `reason="ImagePullBackOff"`。
- **现象解释**：由于域名无效，集群 DNS (127.0.0.53) 无法解析该主机名，导致 `kubelet` 无法建立网络连接以拉取镜像，从而进入 Back-off 重试并最终表现为 Pod 处于 `Pending` 和 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 55.7s
├─ 问题定位: 17.5s
├─ 并发证据采集: 30.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 30.3s (Evidence 23.4s, RCA 6.8s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
