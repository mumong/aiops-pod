## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，镜像 registry.invalid/aiops/workload:missing 拉取失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `rpc error: code = Unknown desc = ... failed to resolve reference "registry.invalid/aiops/workload:missing": failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接定位镜像拉取失败的深层网络原因：DNS 解析失败 |
| 2 | K8s Event | kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (x152 over 39m) | 确认镜像拉取失败的持续性与频率 |
| 3 | K8s State | kubernetes | `pod.status: Pending` | 描述异常容器的当前生命周期状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 通过监控指标确认容器处于等待镜像拉取的阶段 |

**证据说明：**
Kubernetes 事件事实 #1 提供了决定性的网络错误堆栈，明确指出了是向集群 DNS `127.0.0.53:53` 查询 `registry.invalid` 时发生了 `no such host` 错误，这构成了拉取失败的直接技术根因。Kubernetes 事件事实 #2 和 Metric 事实 #4 相互印证，证实了该 DNS 解析失败导致的镜像拉取是一个持续近 40 分钟的阻断性状态。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS (127.0.0.53) 无法解析 registry.invalid → kubelet 发起镜像拉取请求失败 (DNS lookup failed) → 容器状态转变为 ImagePullBackOff → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是**集群 DNS (CoreDNS) 中缺乏 `registry.invalid` 的解析记录，导致 kubelet 无法解析该镜像仓库域名**。

*   **根因机制**：如证据 #1 所示，kubelet 在尝试下载 `registry.invalid/aiops/workload:missing` 镜像时，触发了底层网络请求。由于本地 DNS 服务器 (`127.0.0.53`) 返回了 `no such host` 错误，导致 HTTP 请求直接失败，无法获取镜像的 manifest。
*   **现象印证**：由于拉取请求反复失败，kubelet 进入了指数退避重试机制（证据 #2），并通过 `Waiting` 状态（证据 #4）将 Pod 维持在 `Pending` 阶段（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.1m
├─ 问题定位: 22.8s
├─ 并发证据采集: 576.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 576.4s (Evidence 566.9s, RCA 9.3s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
