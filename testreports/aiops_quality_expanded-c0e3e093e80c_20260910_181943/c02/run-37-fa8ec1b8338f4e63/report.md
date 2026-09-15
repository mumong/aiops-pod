## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod 配置了无效的镜像仓库域名 (registry.invalid)，导致 Kubelet 在拉取镜像时发生 DNS 解析失败 (no such host)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_message` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认镜像拉取被退避，镜像名含 `registry.invalid` |
| 2 | K8s State | `container.waiting_reason` | `ImagePullBackOff` | 定义当前异常终止状态 |
| 3 | K8s Event | `Failed` Event (fact-b32a888e3463) | `Error: ErrImagePull... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 核心因果链：DNS 解析失败，证实域名无效 |
| 4 | K8s State | `pod.phase` / `pod.status` | `Pending` | 集群调度层将 Pod 维持在 Pending 状态等待就绪 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `1` (labels: `reason="ImagePullBackOff"`) | 从指标侧印证 `ImagePullBackOff` 状态持续存在 |

**证据关联说明：**
K8s Event (#3) 提供了直接的底层错误 (DNS `no such host`)，完美解释了 K8s State (#2, #1) 中的 `ImagePullBackOff` 状态。Metric (#5) 作为辅助观测，确认了这一状态在指标系统中被正确采集且未发生变化。由于容器未启动，无 Logging 和 Tracing 数据。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了无效镜像域名 (registry.invalid) → Kubelet 尝试拉取并遭遇 DNS 解析失败 (no such host) → 镜像拉取失败并触发退避机制 (ImagePullBackOff) → Pod 卡在 Pending 状态，应用不可用
```

### 根因结论
已确认根因为 **镜像配置错误** (事实编号 #1, #3)。

具体表现为：Pod 中的容器被配置为拉取域名 `registry.invalid` 下的镜像。Kubelet 在执行拉取操作时，因该域名在集群 DNS (127.0.0.53:53) 中无法解析 (`no such host`)，导致底层镜像拉取协议失败。这一网络配置/配置错误直接引发了 `ImagePullBackOff` 异常状态，并阻止了 Pod 进入 Running 阶段。现有证据已充分支持该结论，无需补充决定性的日志或 Trace 数据。

---

## 📊 性能统计

```text
├─ 总耗时: 56.9s
├─ 问题定位: 14.7s
├─ 并发证据采集: 33.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 33.5s (Evidence 29.7s, RCA 3.7s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
