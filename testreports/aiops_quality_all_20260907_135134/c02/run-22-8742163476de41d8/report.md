## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态: `waiting`, `reason`: `ImagePullBackOff` (`fact-012c38f110ea`) | 确认当前 Pod 无法启动的直接状态 |
| 2 | K8s Event | Kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (`fact-32834fd8094f`) | 反映 kubelet 在多次拉取失败后已进入退避期 |
| 3 | K8s Config | Kubernetes | 容器 `app` 镜像地址为 `registry.invalid/aiops/workload:missing` (`fact-b31192689a79`) | 提供故障触发的具体配置源头 |
| 4 | K8s Event | Kubernetes | `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (`fact-b31192689a79`) | 提供根本失败的直接证据：DNS 无法解析该域名 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` (`fact-533c823cbafd`) | 独立验证容器目前确实卡在 ImagePullBackOff |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` (`fact-275ded1ac7dc`) | 证实容器从未成功启动过，排除了启动后崩溃的情况 |

**证据说明：**
Kubernetes 事件与状态事实互相印证：配置了无效域名 `registry.invalid`（证据 #3），导致 kubelet 在查询本地 DNS `127.0.0.53:53` 时明确报错 `no such host`（证据 #4）。该 DNS 解析失败直接导致镜像拉取请求终止，进入 `ImagePullBackOff` 状态（证据 #1、#2）。Metrics 独立观测到的 `waiting_reason`（证据 #5）和 `restart_count=0`（证据 #6）确认了 Pod 持续处于拉取失败阶段且未发生过任何启动成功，进一步限定了故障停留在网络/配置层。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了保留域名 registry.invalid 作为镜像仓库地址 → kubelet 向节点 DNS (127.0.0.53:53) 解析失败，返回 no such host → 镜像拉取请求失败并进入 Back-off 退避 → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因为 **Pod 配置引用了无效的镜像仓库域名 `registry.invalid`**（证据 #3、#4）。

该域名在集群配置的 DNS (`127.0.0.53`) 中无法解析（证据 #4），导致 kubelet 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时发生网络错误。该失败触发了容器的 `ImagePullBackOff` 状态（证据 #1、#2），使得 Pod 无法进入 Running 状态（证据 #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.2s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 38.1s (Evidence 31.2s, RCA 6.8s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
