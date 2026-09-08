## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，应用容器 app 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: ImagePullBackOff` (x6), `Back-off pulling image "registry.invalid/aiops/workload:missing"` (x109) | 直接呈现 Pod 无法启动的实时症状与重试频率 |
| 2 | K8s Event | Kubernetes | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供底层根因：DNS 解析失败导致镜像拉取中断 |
| 3 | K8s State | Kubernetes | `waiting_reason: "ImagePullBackOff"`, `waiting_message: "Back-off pulling image ..."` | 固化容器当前的阻塞状态 |
| 4 | K8s State | Kubernetes | `phase: "Pending"`, `pod.status: "Pending"`, `ContainersReady: False` | 证实 Pod 未进入运行阶段，无业务流量发生 |
| 5 | K8s Config | Kubernetes | 资源申请：CPU `5m` / Memory `8Mi`；资源限制：CPU `50m` / Memory `32Mi` | 排除因资源不足导致 Pod 无法调度的可能性 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (sample_count: 1) | 监控层侧向印证容器处于异常等待状态 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除容器启动后崩溃重启（CrashLoopBackOff）的可能 |

**证据小结**：
K8s 事件与状态均指向镜像拉取阻塞，Prometheus 指标独立确认了等待状态；日志与链路追踪未提供数据（因容器未启动），且故障现象属于部署阶段的网络与配置问题，非业务逻辑或资源过载问题。所有事实均指向镜像配置异常。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置 registry.invalid/aiops/workload:missing 包含无效域名 → kubelet 执行 DNS 查询失败 (lookup registry.invalid: no such host) → 镜像拉取持续失败触发 Back-off 机制 → Pod 锁定在 ImagePullBackOff 状态
```

### 根因结论

已确认根因是 **Pod 配置了无效的镜像仓库域名 (`registry.invalid`)**。

Kubelet 在尝试拉取镜像时，因该域名无法被 DNS 解析（`no such host`），导致镜像拉取操作直接失败并触发 `ErrImagePull`。随后的重试行为不断累积并转化为 `ImagePullBackOff` 状态。这一网络配置错误阻断了容器的启动流程，且由于容器从未成功启动，未产生相关的业务日志或 Trace 数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 10.9s
├─ 并发证据采集: 76.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 76.6s (Evidence 66.9s, RCA 9.5s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- 未调用 Runbook
