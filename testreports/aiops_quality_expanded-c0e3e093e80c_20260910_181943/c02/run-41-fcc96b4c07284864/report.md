## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b in aiops-case-02 is stuck in ImagePullBackOff/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... Head "https://registry.invalid/v2/...": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-af7dbe44d5ff) | 直接证实镜像拉取失败原因：DNS 查询 `registry.invalid` 失败，域名无法解析。 |
| 2 | K8s State | Kubernetes | Pod Phase: `Pending` (fact-5fc865f34860)；Container Waiting Reason: `ImagePullBackOff` (fact-d5cde93c5656) | 确认故障现象，Pod 因无法拉取镜像而处于等待状态。 |
| 3 | K8s Config | Kubernetes | Container Image: `registry.invalid/aiops/workload:missing` (fact-1342b10ccfae) | 提供故障根源的具体对象，即配置中使用了无效的镜像域名。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = 1 (fact-ec8883ac0396) | 独立监控指标佐证 Pod 处于 ImagePullBackOff 状态，与 K8s 事实一致。 |

**证据关联说明：**
K8s 事件（#1）明确指出了失败的具体机制是 DNS 解析错误，直接锁定了配置中的镜像地址（#3）为无效。K8s 状态（#2）与 Prometheus 指标（#4）在现象层面相互印证，确认了该无效配置直接导致了容器的持续拉取失败和 Pending 状态。由于容器未启动，Log 和 Tracing 维度不可用，诊断证据闭环完整。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 配置了不可达的镜像域名 'registry.invalid' → kubelet 尝试拉取镜像并进行 DNS 查询 → 节点 DNS (127.0.0.53) 返回 'no such host' → 镜像拉取失败，Pod 进入 ImagePullBackOff 和 Pending 状态
```

### 根因结论

已确认根因为：**Pod 配置引用了无效或无法解析的容器镜像注册表 URL**。

具体证据如下：
- **配置层面**：Pod 的 `app` 容器配置了镜像 `registry.invalid/aiops/workload:missing`（证据 #3）。
- **故障机制**：Kubelet 在拉取镜像时向节点 DNS 服务器（127.0.0.53）发起查询，但 `registry.invalid` 无法被解析（证据 #1）。
- **最终结果**：由于镜像无法获取，Pod 被调度器挂起在 `Pending` 状态，且容器处于 `ImagePullBackOff`（证据 #2, #4）。

该故障完全由镜像地址配置错误引起，集群内部组件（网络、调度、存储等）均运行正常，属于应用部署层面的配置缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.2s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 43.1s (Evidence 31.9s, RCA 11.1s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
