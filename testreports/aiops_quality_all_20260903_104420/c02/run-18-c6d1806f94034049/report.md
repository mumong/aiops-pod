## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-c7803518aad0` | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确证 DNS 解析失败是导致镜像拉取报错的直接技术原因。 |
| 2 | K8s Event | `fact-24cd8c75f24f` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (175次 over 43m) | 证实拉取动作已多次重试并进入指数退避状态，持续影响服务可用。 |
| 3 | Metric | `fact-48a6888fbc2d` | `kube_pod_container_status_waiting_reason` = 1 (reason: ImagePullBackOff) | 监控层面量化证实 Pod 容器处于 ImagePullBackOff 状态。 |
| 4 | Metric | `fact-37c277ab5fa9` | `kube_pod_container_status_restarts_total` = 0 | 证实容器从未成功启动，排除了因应用崩溃导致重启的可能。 |
| 5 | K8s State | `fact-bb5bc3621018` | `pod.status` = `Pending` | 确认 Pod 因无法拉取镜像停留在 Pending 阶段，未能进入 Scheduling/Running 状态。 |

**证据说明**：
Metrics 明确记录了 `ImagePullBackOff` 状态及零重启，与 Kubernetes Event 中的失败重试行为完全对应。K8s 事件 `fact-c7803518aad0` 提供的底层 `DNS lookup` 错误原文，精准锁定了 `registry.invalid` 域名无法解析是导致拉取失败的根本原因，其他证据均在此基础之上呈现后果。

## 🎯 根因分析 · g1

### 因果链

```text
镜像地址 registry.invalid 配置错误（无效域名） → kubelet 发起镜像拉取请求时 DNS 解析失败（lookup registry.invalid on 127.0.0.53:53: no such host） → 无法从仓库拉取镜像并解包 → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因是 **Pod 容器镜像仓库域名配置错误**。

1. **失效的镜像配置**：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 被配置使用 `registry.invalid/aiops/workload:missing` 作为镜像地址。
2. **底层网络错误**：如证据 #1 (fact-c7803518aad0) 所示，kubelet 在尝试拉取该镜像时，因 `registry.invalid` 为无效测试域名，导致 DNS 解析失败（`no such host`），无法获取镜像清单。
3. **最终现象**：由于镜像拉取持续失败，Pod 进入 `ImagePullBackOff` 状态（证据 #3 fact-48a6888fbc2d 和 #5 fact-bb5bc3621018），且因从未成功启动，其重启次数始终为 0（证据 #4 fact-37c277ab5fa9）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.8s
├─ 并发证据采集: 61.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 61.6s (Evidence 52.1s, RCA 9.4s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
