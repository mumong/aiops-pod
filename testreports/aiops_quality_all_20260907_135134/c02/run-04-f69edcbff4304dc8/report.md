## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod配置了无效的镜像仓库域名'registry.invalid'，且集群DNS无法解析该域名，导致镜像拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Error: ErrImagePull` (fact-4f87234f5e19, x4) | 记录镜像拉取初步失败的警告事件，表明 Pull 动作已受阻。 |
| 2 | K8s Event | `kubelet` | `Error: ImagePullBackOff` (fact-d8eb2aa53338, x6) | 记录拉取被退避的警告事件，表明反复尝试失败后进入等待状态。 |
| 3 | K8s Event | `kubelet` | `Error: ... failed to resolve reference "registry.invalid/aiops/workload:missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-dd73f3579f56, x4) | **核心证据**，明确指出了容器运行时解析域名失败的具体错误堆栈与 DNS 目标。 |
| 4 | K8s State | `container` | `Waiting Reason: ImagePullBackOff` (fact-542ef0372cc7) | 确认容器当前实际生命周期状态。 |
| 5 | K8s State | `container` | `Waiting Message: Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-58edd8176840) | 确认等待拉取的具体镜像名称。 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` (fact-c2288f19993f) | 从监控侧独立印证容器处于 ImagePullBackOff 状态。 |

**证据关联说明**：
1. Kubernetes 事件（事实 #3）中的详细错误堆栈直接锁定了故障原因为 DNS 解析失败，与镜像名称（事实 #5）结合，表明 Pod 配置的 `registry.invalid` 域名无法被集群 DNS (`127.0.0.53`) 解析。
2. Prometheus 监控指标（事实 #6）与容器状态（事实 #4）完全一致，交叉验证了该异常是持续存在的真实状态，而非瞬时抖动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 'registry.invalid' 作为镜像仓库地址 → 集群 DNS (127.0.0.53) 解析失败 (no such host) → kubelet 镜像拉取重试耗尽并退避 (BackOff) → Pod 卡在 Pending 状态，容器处于 ImagePullBackOff
```

### 根因结论

已确认的根因为：**Pod 配置的容器镜像仓库域名 (`registry.invalid`) 无效或不存在，且集群 DNS 服务无法解析该域名。**

**证据支撑**：
- 容器事件（事实 #3）提供了最直接的失败归因，明确报告了 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`，说明底层网络通信未发生，而是域名解析环节直接阻断。
- 容器状态（事实 #4、#5）及监控指标（事实 #6）一致确认了该拉取失败导致的 `ImagePullBackOff` 现象。
- 容器未启动（重启次数为 0，事实 #07a9b2e7fcc7），故无法通过日志或 Trace 进一步排查镜像内部逻辑，故障完全处于启动前的拉取阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 58.8s
├─ 问题定位: 20.2s
├─ 并发证据采集: 26.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 26.7s (Evidence 20.2s, RCA 6.1s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
