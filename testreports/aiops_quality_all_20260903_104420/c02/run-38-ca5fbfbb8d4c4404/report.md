## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Normal BackOff 3m11s (x328 over 78m) kubelet Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-65fff0cd1c26) | 核心证据：明确记录 kubelet 拉取镜像被阻断，且已进行 78 分钟的指数退避。 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `ImagePullBackOff`; `container.waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-944c58dffe41, fact-a229c7f3723f) | 核心证据：容器当前确切状态为拉取失败。 |
| 3 | K8s State | kubernetes | `pod.phase`: `Pending`; `pod.status`: `Pending`; `ContainersReady`: `False` (fact-76cabba0dc11, fact-86136abe3967, fact-0d946080db37) | 直接现象：Pod 卡在 Pending 阶段，容器未就绪。 |
| 4 | K8s Event | kubernetes | `Reason: ImagePullBackOff` (fact-10d7fb1a8516) | 辅助印证：Pod 事件详情中的失败原因。 |
| 5 | K8s Config | kubernetes | `container.resource_limit.cpu`: `50m`; `container.resource_request.cpu`: `5m`; `memory_request`: `8Mi`, `memory_limit`: `32Mi` (fact-0b8aa74c9218, fact-23c2179d67c8, fact-299c22d5eb96, fact-2d31bf29e5df) | 上下文信息：资源请求与限制配置正常，排除了因资源不足导致调度失败的可能性。 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason="ImagePullBackOff", value=1, sample_count=1) (fact-b7631d1769a2) | 辅助印证：监控指标直接映射到 ImagePullBackOff 状态。 |

**证据关联说明：**
Kubernetes 事件与状态事实（#1, #2, #4）在长达 78 分钟的时间窗口内持续记录，且数值上指标状态（#6）与之完全吻合。所有证据共同指向单一事实：Pod 无法拉取名为 `registry.invalid/aiops/workload:missing` 的镜像，且因配置了指数退避策略而长期处于 `ImagePullBackOff` 状态。日志与追踪数据（Logging/Tracing）因容器未能启动而不可用。

## 🎯 根因分析 · g1

### 因果链

```text
镜像定义引用了无效域名 'registry.invalid' 且缺失 imagePullSecrets → kubelet 拉取镜像被持续阻断 → Kubernetes 进入 ImagePullBackOff 状态 → Pod 处于 Pending 状态，容器未启动
```

### 根因结论

**已确认的根因：** Pod `aiops-case-02/workload-65b7f54794-rnlv4` 配置了无效的镜像仓库域名 `registry.invalid`。

**分析说明：**
证据 `fact-65fff0cd1c26` 和 `fact-a229c7f3723f` 显示，`kubelet` 持续尝试拉取镜像 `registry.invalid/aiops/workload:missing` 并因网络或凭证问题失败，随后触发 `BackOff` 机制。这导致容器始终无法启动，Pod 状态被维持在 `Pending`。集群资源（#5）正常，排除资源瓶颈；缺失的镜像 Pull Secret 或未修正的域名是阻断拉取的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 21.1s
├─ 并发证据采集: 119.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 119.6s (Evidence 109.4s, RCA 10.0s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
