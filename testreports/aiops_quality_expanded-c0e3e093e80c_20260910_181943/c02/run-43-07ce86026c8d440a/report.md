## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态，无法启动容器 app |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `Pending` (fact-7dd6d87d9e0e) | 确认 Pod 处于异常等待状态 |
| 2 | K8s Event | kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-076d94e31946) | 记录容器运行时尝试拉取失败后的退避行为 |
| 3 | K8s Event | kubernetes | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-9fac6d6831c1) | 记录具体的 DNS 解析失败及关联的 Pod IP/Container ID (fact-927d1d02fe85) |
| 4 | K8s Config | kubernetes | Container `app` memory limit `32Mi`, cpu limit `50m` (fact-500c303e7dcf) | 排除因资源限额过小导致容器启动失败的可能性 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，label `reason=ImagePullBackOff` (fact-dd0d1878d5a9) | 指标确认等待原因为镜像拉取失败 |

现有证据显示，Kubernetes 事件中的 DNS 解析失败日志（#3）直接解释了指标中报告的拉取失败原因（#5）。由于 Pod 从未成功启动，Logging 和 Tracing 维度数据为空，当前证据已完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS (127.0.0.53) 无法解析 registry.invalid 域名 → kubelet 发起的 image pull 请求因 DNS 失败而中止 → 镜像拉取失败，Pod 状态转为 ImagePullBackOff
```

### 根因结论

已确认的根因是：Pod 配置的容器镜像 `registry.invalid/aiops/workload:missing` 中的域名 `registry.invalid` 在集群 DNS (127.0.0.53) 中无法解析。
根据 K8s Event (fact-9fac6d6831c1)，kubelet 在尝试解析该域名时遇到了 `no such host` 错误，导致无法建立网络连接以拉取镜像。该网络层故障直接导致了当前 Pod 的 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.7s
├─ 并发证据采集: 31.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 31.4s (Evidence 24.2s, RCA 7.1s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
