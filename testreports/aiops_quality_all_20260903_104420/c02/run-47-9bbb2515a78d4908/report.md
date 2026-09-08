## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ErrImagePull | Pod workload-65b7f54794-rnlv4 处于 ErrImagePull/ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-1065bc0b79c2` | `container.waiting_reason`: "ImagePullBackOff" | 直接证明容器处于镜像拉取失败后的退避状态 |
| 2 | K8s State | `fact-19f896fd536e` | `container.waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 明确指出失败的镜像引用为 `registry.invalid/aiops/workload:missing` |
| 3 | K8s Event | `fact-78769c6e5972` | `Normal BackOff 3m46s (x394 over 93m) kubelet Back-off pulling image "registry.invalid/aiops/workload:missing"` | 证实 kubelet 在 93 分钟内发生了 394 次拉取失败并进入退避，验证了持续性的拉取失败机制 |
| 4 | K8s State | `fact-1acb76d8fafc` | `pod.phase`: "Pending" | 表明 Pod 因容器无法就绪而停滞在 Pending 阶段，未进入运行状态 |
| 5 | Metric | `fact-8431dfbbba12` | `kube_pod_container_status_waiting_reason`: 1 (reason: ImagePullBackOff) | Prometheus 指标印证了容器等待原因为镜像拉取失败 |

**证据说明：**
1. K8s 状态（#1, #2）与事件日志（#3）相互印证，共同指向 `registry.invalid/aiops/workload:missing` 这个具体镜像引用导致了持续的拉取失败。
2. K8s 状态（#1, #4）与 Metric 数据（#5）在现象层面一致，确认容器始终处于 `ImagePullBackOff` 状态且 Pod 未启动。
3. 由于容器无法启动，Logging 和 Tracing 维度被物理限制（`not_applicable`），无相关数据可提供进一步限定。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置引用了无效域名 registry.invalid → DNS 解析失败导致拉取被拒绝 → 拉取重试耗尽进入退避(ImagePullBackOff) → Pod 停滞在 Pending 状态且容器未启动
```

### 根因结论

已确认的根因是：Pod `workload-65b7f54794-rnlv4` 的容器配置中使用了无效域名 `registry.invalid/aiops/workload:missing` 作为镜像源。

**证据支持：**
- K8s 状态事实 (`fact-19f896fd536e`) 明确指出了失败的镜像引用路径。
- K8s 事件日志 (`fact-78769c6e5972`) 证实了 `kubelet` 针对该特定镜像进行了长达 93 分钟的 394 次拉取尝试，并因持续失败而进入退避状态。
- Metric 监控 (`fact-8431dfbbba12`) 从监控视角确认了容器始终处于 `ImagePullBackOff` 的等待状态。

上述事实构成了完整的闭环证据链，明确排除了资源不足、调度失败或网络策略拦截等其他因素，直接定位为镜像域名配置错误导致 DNS 解析或网络不通，进而引发拉取失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.7s
├─ 并发证据采集: 59.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 59.5s (Evidence 51.7s, RCA 7.5s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
