## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod 的镜像引用 `registry.invalid/aiops/workload:missing` 使用了无效的域名 `registry.invalid`，导致 kubelet 无法通过 DNS 解析仓库地址（no such host），从而引发 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-30fcf5c3e84b) | 确认 kubelet 在拉取指定镜像时遭遇 DNS 解析失败，导致请求被终止。 |
| 2 | K8s Event | `kubelet` | `Error: ImagePullBackOff` (fact-a0c1cd15dc0a) | 确认 K8s 控制器已根据拉取失败将容器状态标记为 ImagePullBackOff。 |
| 3 | K8s State | `pod` | `pending` (fact-06bad75b171c) | 确认 Pod 当前处于 Pending 状态，尚未进入运行或失败终止阶段，符合镜像拉取受阻的状态。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-1563c079f425) | 确认该 Pod 仍处于 Waiting 状态且原因是 ImagePullBackOff，与 Event 状态一致。 |

Kubernetes 事件明确记录了镜像拉取时的具体错误原因为 DNS 解析失败（`no such host`），Metric 状态（fact-4）在数值层面佐证了 Event 中的 `ImagePullBackOff` 状态，两者互相印证了拉取失败并导致 Pod 停滞的现状。

## 🎯 根因分析 · g1

### 因果链

```text
镜像引用了无效域名 registry.invalid → kubelet DNS 解析失败 (no such host) → 镜像拉取终止 (ImagePullBackOff) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod 中容器引用的镜像地址 `registry.invalid/aiops/workload:missing` 包含无效的域名 `registry.invalid`。

事实依据如下：
*   **DNS 解析失败**：事实 #1 (fact-30fcf5c3e84b) 显示 kubelet 尝试通过 `127.0.0.53:53` 解析 `registry.invalid` 时返回 `no such host`，证明该域名不可达。
*   **状态一致性**：事实 #2 (fact-a0c1cd15dc0a) 和事实 #4 (fact-1563c079f425) 分别从 K8s Event 和 Prometheus Metric 两个独立维度证实，容器当前确实停留在 `ImagePullBackOff` 的等待状态，符合拉取失败的预期表现。

现有证据链完整，无需补充决定性事实即可确认是镜像配置错误导致的拉取失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.9s
├─ 并发证据采集: 55.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 55.8s (Evidence 48.5s, RCA 7.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
