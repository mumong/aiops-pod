## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv (aiops-case-02) 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` (Warning) | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": rpc error ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-5b38a9ca5cb4) | 提供直接错误栈：DNS 解析失败导致镜像拉取中断。 |
| 2 | K8s Event | `kubelet` (Warning) | `Warning Failed ... Error: ErrImagePull` (fact-88b7b720bf90) | 确认 K8s 层面的拉取错误结果。 |
| 3 | K8s Event | `kubelet` (Normal) | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-1e1799607ebd) | 展示拉取失败后的重试退避行为。 |
| 4 | K8s State | Pod Status | `status: Pending`, `reason: ImagePullBackOff` (fact-491608e606d1, fact-47c452b0ba85) | 定义当前阻塞现象。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason[reason="ImagePullBackOff"] = 1` (fact-c13933a49195) | 独立量化证实了 Pod 处于 ImagePullBackOff 状态的客观指标。 |

**证据关联：**
K8s Event 中的 `dns: no such host` 错误与 Metric 中的 `waiting_reason=ImagePullBackOff` 直接对应。Metric 提供了客观的数值快照，印证了 Event 所反映的持续异常状态，排除了因网络瞬时抖动导致单点失败的可能。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 spec 使用虚构域名 registry.invalid → 节点 DNS 解析失败 (no such host) → 镜像拉取请求失败 → Pod 进入 ImagePullBackOff 状态
```

### 根因结论
已确认根因为 **Pod 配置了无效的镜像仓库域名 'registry.invalid'** (参考证据 #1)。
该域名在节点网络中无法解析，导致 kubelet 无法获取镜像，进而使 Pod 维持在 `ImagePullBackOff` 状态 (参考证据 #3, #4, #5)。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 18.7s
├─ 并发证据采集: 557.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 557.4s (Evidence 550.0s, RCA 7.2s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
