## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: `ImagePullBackOff` | 定义当前 Pod 核心异常状态 |
| 2 | K8s Event | Kubernetes | `Failed to pull image ...: failed to resolve reference ...: dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供 DNS 解析失败的直接错误堆栈 |
| 3 | K8s State | Kubernetes | pod.status: `Pending`, pod.condition: `ContainersNotReady` | 确认 Pod 持续处于未就绪的阻塞状态 |
| 4 | K8s Config | Kubernetes | 镜像源: `registry.invalid/aiops/workload:missing` | 标识触发拉取的无效资源标识符 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason=`ImagePullBackOff`) | 量化证实拉取失败处于持续挂起状态 |

**证据关联说明：**
Kubernetes 层面，K8s Event (#2) 记录了具体的网络层报错（DNS 无法解析 `registry.invalid`），直接印证了 K8s State (#1) 中 `ImagePullBackOff` 的根本原因是解析失败。Metric (#5) 从监控指标侧确认了该状态已稳定持续。Pod 配置 (#4) 提供的镜像域名在 DNS 查询中无效，逻辑闭环成立。由于容器未启动，Logging/Tracing 维度无数据产生，不影响根因定性。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid 无法解析(DNS no such host) → kubelet 拉取镜像失败 → 容器启动受阻进入重试退避 → Pod 持续 ImagePullBackOff/Pending
```

### 根因结论

已确认根因为：**Pod 配置的镜像仓库域名 `registry.invalid` 无效或集群内不可达。**

证据链表明，kubelet 在尝试拉取 `registry.invalid/aiops/workload:missing` 时遭遇了 DNS 解析失败（`lookup ... no such host`），导致镜像拉取报错并进入 `ImagePullBackOff` 状态，进而导致 Pod 阻塞在 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.9s
├─ 并发证据采集: 42.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 42.2s (Evidence 34.2s, RCA 7.9s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
