## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | workload-65b7f54794-jmq6b 持续处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Error: ImagePullBackOff`; `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接指出镜像拉取失败的机制是 DNS 解析无效域名失败 |
| 2 | K8s State | `pod.phase/status` | `phase: Pending`; `status: ImagePullBackOff` | 确认 Pod 长期停滞在拉取镜像阶段，未进入运行态 |
| 3 | K8s Event | `kubelet` | `Normal BackOff 5m2s (x44 over 15m) ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 反映 kubelet 因连续失败已进入指数退避重试周期 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` 返回 `1`，标签 `reason: ImagePullBackOff` | 独立于 K8s API 指标源确认当前正等待 ImagePull 异常 |

证据 1 中的 DNS 查询失败（`no such host`）直接解释了证据 2 和 3 中容器无法启动、持续退避的状态；证据 4 通过监控指标独立印证了这一故障的当前有效性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 配置无效域名 registry.invalid/aiops/workload:missing → DNS 解析失败 (no such host) 导致拉取请求终止 → 容器保持 Pending / ImagePullBackOff 状态 → kubelet 持续退避重试，应用不可用
```

### 根因结论

已确认根因为 **Pod 配置了无效的镜像仓库域名 `registry.invalid`**。事实证据 #1 明确显示，kubelet 尝试拉取该镜像时，DNS 解析返回 `no such host`（查询 `127.0.0.53:53`），证实了目标仓库在集群网络中不可达。这导致了镜像拉取动作持续失败，触发 K8s 的 `ImagePullBackOff` 状态（事实证据 #2、#3）并被 Prometheus 指标确认（事实证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 29.0s
├─ 并发证据采集: 102.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 102.7s (Evidence 95.3s, RCA 7.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
