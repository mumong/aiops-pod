## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | workload-65b7f54794-nqrzv 处于 ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `rpc error: code = Unknown desc = failed to pull and unpack image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 揭示直接失败机制：DNS 解析彻底失败，无法建立网络连接。 |
| 2 | K8s State | Kubernetes | 镜像拉取状态：`ImagePullBackOff`；Pod 状态：`Pending` | 确认当前异常状态，说明 kubelet 因持续失败而进入退避重试。 |
| 3 | K8s Config | Kubernetes | 容器镜像配置：`registry.invalid/aiops/workload:missing` | 定位故障源头为无效且不存在的注册表域名 `registry.invalid`。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = `1` | 独立于 K8s Event 的监控确认，佐证容器处于等待镜像拉取完成的阻塞状态。 |

**证据说明**：
Kubernetes Event 提供了最直接的失败证据，明确指出在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时，底层发生了 `lookup registry.invalid on 127.0.0.53:53: no such host` 错误。Metric 的 `waiting_reason` 与 Kubernetes 的 `ImagePullBackOff` 状态完全一致，相互印证了容器因无法获取镜像而处于等待状态的事实。由于容器始终未能启动，Logging 和 Tracing 数据为空，排除了应用层面的运行时错误，确认故障发生在调度与拉取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
镜像引用域名 'registry.invalid' 不可达（未配置或不存在的内网域名） → DNS 解析失败导致网络握手无法发起 → 镜像拉取被强制中断并进入退避（BackOff） → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因为 **Pod 部署配置中使用了无效的镜像域名 `registry.invalid`**。

事实表明，该域名无法被解析，且未指向任何有效的 Docker Registry。根据真实工具事实 `fact-6b8dc938c586`，kubelet 尝试通过 `https` 协议请求镜像 Manifest 时，因 DNS 查询返回 `no such host` 而直接失败，导致镜像拉取失败（`ErrImagePull`）并迅速进入退避状态（`BackOff`）。目前证据已确凿，无需更多事实即可定论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.9s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 38.3s (Evidence 30.9s, RCA 7.2s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
