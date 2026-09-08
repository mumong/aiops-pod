## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态，未进入 Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-109ab8af2661) | `container.waiting_reason`: `ImagePullBackOff` (container: app) | 确诊容器因镜像拉取失败处于重试退避状态 |
| 2 | K8s State | kubernetes (fact-18edfc771f73) | `container.waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 锁定导致拉取失败的无效镜像地址 `registry.invalid` |
| 3 | K8s Event | kubernetes (fact-81b970a67d84) | `BackOff`: 4m23s (x328 over 79m) 拉取镜像 "registry.invalid/aiops/workload:missing" | 提供长期持续失败的上下文，证明异常已持续 79 分钟 |
| 4 | K8s State | kubernetes (fact-315b0027b2c4) | `pod.status`: `Pending` | 确认 Pod 未进入运行阶段，停留在调度后的等待状态 |
| 5 | Metric | prometheus (fact-0e0e7515c6cb) | `kube_pod_container_status_waiting_reason` = 1, labels: `reason: ImagePullBackOff` | 监控指标独立印证了容器的阻塞原因 |

由于容器镜像拉取失败且未启动，日志（Logging）与链路追踪（Tracing）维度均显示 `not_applicable`，无业务日志或 Trace 数据可采集。K8s 事件记录（fact-3c14140447a3 等）主要反映 CNI 网络状态及当前的 ImagePullBackOff 事件，无其他冲突性系统错误。以上 K8s 状态与 Metrics 一致，共同指向镜像配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置包含保留域名 registry.invalid → DNS 解析失败，Kubelet 无法拉取镜像 → 触发指数退避策略 (ImagePullBackOff) → Pod 滞留 Pending 状态，用户可见容器未启动
```

### 根因结论

已确认的根因为 **Pod 配置了无效的镜像仓库域名**。

具体机制是 Pod 的容器定义中指定了镜像地址 `registry.invalid/aiops/workload:missing`，其中 `registry.invalid` 为 RFC 2606 保留的无效域名 [证据 #2]。Kubelet 在尝试拉取该镜像时无法解析域名导致失败，进而进入 `ImagePullBackOff` 等待状态 [证据 #1, #3]。该配置错误直接导致容器无法启动，进而使 Pod 维持在 `Pending` 阶段 [证据 #4]。Prometheus 指标中 `waiting_reason` 为 `ImagePullBackOff` 的结果 [证据 #5] 进一步证实了这一结论。目前证据链完整，无缺失决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.7s
├─ 并发证据采集: 41.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 41.9s (Evidence 33.2s, RCA 8.6s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
