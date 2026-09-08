## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet/container` | Waiting reason: `ImagePullBackOff` | 确认 Pod 当前处于镜像拉取失败后的退避等待状态 |
| 2 | K8s Event | `kubelet` | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (重复 4 次) | 提供决定性证据，指出镜像仓库域名无法解析，且 kubelet 正在重试拉取 |
| 3 | K8s State | `kubelet/container` | Waiting message: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 进一步证实 Pod 因无法获取指定镜像而处于退避状态 |
| 4 | K8s Event | `kubelet` | `Error: ImagePullBackOff` (重复 6 次) | 描述 Pod 容器最终处于 ImagePullBackOff 状态的系统事件 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1 (Labels: `container="app"`, `reason="ImagePullBackOff"`) | 独立于 K8s API 的指标数据确认应用容器处于等待状态 |
| 6 | K8s State | `kubelet/pod` | Pod 状态: `Pending` (未进入 Running) | 确认故障发生在 Pod 启动阶段，尚未进入运行生命周期 |
| 7 | K8s Config | `k8s manifest` | CPU Limit: `50m`, Memory Limit: `32Mi` | 确认资源配额极小，排除因资源超限导致的拉取失败 |
| 8 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 0 | 确认该容器没有发生过成功启动后的重启，排除健康度问题 |

**证据印证说明：**
Kubernetes API 事件与 Metrics 指标高度一致，共同确认应用容器 `app` 处于 `ImagePullBackOff` 状态。决定性的诊断线索来自 K8s 事件日志（编号 2 和 4），明确指出失败原因是 `registry.invalid` 域名 DNS 解析失败（`no such host`），结合 K8s 配置（编号 7），证实故障源于镜像仓库地址配置无效，与资源限制无关。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名配置无效 (registry.invalid) → DNS 解析失败 (no such host) → 镜像拉取失败并进入 Back-off 重试 → Pod 保持 Pending 及 ImagePullBackOff 状态
```

### 根因结论

已确认根因为 **镜像仓库配置使用了无效域名**。
Pod `workload-65b7f54794-rnlv4` 配置了 `registry.invalid/aiops/workload:missing` 作为镜像地址，该域名在集群环境中无法通过 DNS (127.0.0.53) 解析。这导致 kubelet 在尝试拉取镜像时遭遇网络层失败（`dial tcp: lookup ... no such host`），随后触发重试退避机制（`Back-off pulling image`），最终使 Pod 维持在 `Pending` 和 `ImagePullBackOff` 状态，未能进入运行阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.1s
├─ 并发证据采集: 46.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 46.9s (Evidence 38.7s, RCA 8.0s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
