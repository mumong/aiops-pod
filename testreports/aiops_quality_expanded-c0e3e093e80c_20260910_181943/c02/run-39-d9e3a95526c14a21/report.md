## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Spec | `container.waiting_reason`: "ImagePullBackOff"; `container.waiting_message`: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 确认应用容器 `app` 处于镜像拉取失败后的退避阶段 |
| 2 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 揭示镜像拉取失败的直接网络原因是无法解析域名 `registry.invalid` |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff", container="app"} = 1` | 从指标维度验证容器确实处于 ImagePullBackOff 状态 |
| 4 | K8s State | Pod Status | `pod.phase`: "Pending"; `pod.condition.Ready`: "False" | 确认 Pod 因容器启动失败而处于非就绪状态 |

**证据关联说明：**
Kubernetes 事件（#2）中 `no such host` 的报错直接解释了 State 信息中镜像拉取失败的原因，这与 Prometheus 指标（#3）观测到的 `ImagePullBackOff` 状态互相印证。由于容器未能启动，Logging 和 Tracing 维度无数据，故障链在 Kubernetes 层面即可闭环。

## 🎯 根因分析 · g1

### 因果链
```text
镜像配置使用了无效域名 registry.invalid → DNS (127.0.0.53) 无法解析该主机名 → 镜像拉取请求被拒绝 (ImagePullBackOff) → Pod 处于 Pending 状态且容器处于 Waiting 状态
```

### 根因结论
已确认根因为**镜像地址配置错误**。容器配置中指定的镜像地址 `registry.invalid/aiops/workload:missing` 中的域名 `registry.invalid` 无法被集群 DNS (127.0.0.53) 解析，导致 kubelet 无法拉取镜像。该结论由 K8s 事件中的具体 `no such host` 错误原文（证据 #2）及容器状态事实（证据 #1）直接支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.7s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 43.1s (Evidence 35.0s, RCA 7.9s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
