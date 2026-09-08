## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod配置使用了无效的镜像仓库域名(registry.invalid)，且集群DNS无法解析该域名，导致镜像拉取失败并陷入ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认为 DNS 解析失败导致镜像拉取失败 |
| 2 | K8s Event | K8s | `Error: ImagePullBackOff` | 确认最终 Pod 状态 |
| 3 | K8s Event | K8s | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认拉取的具体镜像地址 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 验证 K8s 事件描述的等待原因一致性 |
| 5 | K8s State | K8s | `pod.status = Pending`, `restart_count = 0` | 确认为启动阶段失败，无重启 |

证据表明：Pod 处于 `Pending` 状态，且无任何重启记录。K8s 事件明确指出由于 `lookup registry.invalid on 127.0.0.53:53: no such host` 导致无法拉取镜像 `registry.invalid/aiops/workload:missing`，随后进入 `ImagePullBackOff`。Prometheus 指标中的 `waiting_reason` 与 K8s 事件描述完全一致，佐证了这一诊断事实。

## 🎯 根因分析 · g1

```text
镜像仓库域名无效(registry.invalid) → DNS解析失败(dial tcp: lookup ... no such host) → 镜像拉取失败(Failed to pull image) → Pod状态ImagePullBackOff
```

### 根因结论
已确认根因为 **Pod 配置使用了无效的镜像仓库域名 (`registry.invalid`)**。K8s 事件证据 `fact-8fd5f5d27412` 显示，集群 DNS 服务 (`127.0.0.53`) 无法解析该域名，直接导致镜像拉取失败，进而使 Pod 陷入 `ImagePullBackOff` 状态。Prometheus 指标证据 `fact-30be5edcf455` 进一步证实了 `waiting_reason` 为 `ImagePullBackOff`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.5s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 39.6s (Evidence 34.8s, RCA 4.6s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
