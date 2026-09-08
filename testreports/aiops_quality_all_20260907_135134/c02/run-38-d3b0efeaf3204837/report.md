## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv处于ImagePullBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-3cd50d014952) | 确诊镜像仓库域名 DNS 解析失败的具体错误。 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ImagePullBackOff` (fact-0d475311300f) | 说明容器因拉取失败已进入指数退避重试状态。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-131e2cffc83a) | 验证了容器处于 ImagePullBackOff 状态的持续性。 |
| 4 | K8s State | kubernetes | `pod.phase: Pending`, `ContainersReady: False` (fact-3f2ca3a8618d, fact-ea973ab73bba) | 确认 Pod 因容器未就绪而卡在 Pending 阶段。 |

**证据关联说明：**
Kubernetes 事件中的 `no such host` 直接解释了 K8s 状态 `ImagePullBackOff` 及 Metric 数据 `waiting_reason=ImagePullBackOff` 的成因；所有维度一致指向镜像拉取受阻。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置使用了无效域名 registry.invalid 作为镜像仓库 → kubelet执行镜像拉取时域名DNS解析失败(no such host) → 镜像拉取中断并持续重试导致ErrImagePull转ImagePullBackOff → Pod状态卡在Pending/ContainerWaiting
```

### 根因结论

已确认根因为**镜像仓库域名 `registry.invalid` 无效导致 DNS 解析失败**。

证据支撑：
1. **直接证据**：K8s 事件明确记录了 DNS 查询失败 (`lookup registry.invalid ... no such host`)，证明底层网络解析不可达（见证据 1）。
2. **状态佐证**：容器等待原因 (`ImagePullBackOff`) 和 Pod 状态 (`Pending`) 均与镜像拉取失败导致的容器无法启动现象完全吻合（见证据 2, 4）。
3. **数据一致性**：Prometheus 指标监控到的 `ImagePullBackOff` 计数与 K8s 侧状态保持同步，排除了瞬时波动导致的可能（见证据 3）。

由于容器无法启动，Logging 与 Tracing 维度自然为空，此缺失符合预期，不影响上述结论的成立。

---

## 📊 性能统计

```text
├─ 总耗时: 59.9s
├─ 问题定位: 15.6s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 35.1s (Evidence 28.4s, RCA 6.6s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
