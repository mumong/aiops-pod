## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod 配置了无法通过 DNS 解析的镜像仓库域名（registry.invalid），且未配置 imagePullSecrets，导致 Kubelet 拉取镜像失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | **核心根因**：明确记录 DNS 解析失败，确认镜像仓库不可达 |
| 2 | K8s State | `container` | `reason: "ImagePullBackOff"` | 直接症状：容器因拉取镜像失败进入退避等待状态 |
| 3 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 状态印证：监控系统确认容器处于 ImagePullBackOff 等待中 |
| 4 | K8s Event | `kubelet` | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 过程印证：展示 Kubelet 正在尝试重试拉取该特定镜像 |
| 5 | K8s State | `pod` | `phase: "Pending"`, `ContainersReady: False` | 宏观状态：Pod 调度完成但因容器未就绪而卡在 Pending 阶段 |

**证据关联说明**：
Metric 确认了“ImagePullBackOff”的持续状态，而 K8s Event (fact-1) 揭示了导致该状态的根本机制——DNS 查询返回 `no such host`。Event (fact-4) 进一步证实拉取的对象正是 `registry.invalid/...`，直接指向镜像配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置 registry.invalid (DNS 不可达) → Kubelet 拉取失败 (DNS 解析错误) → 容器无法启动 → Pod 状态为 ImagePullBackOff / Pending
```

### 根因结论

**已确认根因：Pod 配置的容器镜像地址 `registry.invalid/aiops/workload:missing` 对应的域名无法解析。**

*   **事实支撑**：
    1.  Kubernetes Event 明确记录了 `dial tcp: lookup registry.invalid ... no such host`，证明集群内无法通过 DNS 解析该仓库域名 (事实 #1)。
    2.  K8s 状态与 Metric 一致显示容器因镜像拉取失败进入 `ImagePullBackOff` (事实 #2, #3)。
    3.  无其他资源争用或网络策略相关的阻碍证据（Metric 无 Failed 状态，仅 Pending），排除集群层面故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.0s
├─ 并发证据采集: 65.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 65.3s (Evidence 60.9s, RCA 4.3s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
