## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | DNS解析失败导致镜像仓库不可达 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubectl describe pod` | `Error: ImagePullBackOff` / `Error: ErrImagePull` | 呈现容器当前停滞的终态现象 |
| 2 | K8s Event | `kubectl describe pod` | `Head "https://registry.invalid/v2/.../manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 捕获导致状态异常的直接失败机制 |
| 3 | K8s Event | `kubectl describe pod` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 佐证 kubelet 在遭遇重试耗尽后进入退避状态 |
| 4 | K8s State | `kubectl get pod` | `phase: Pending` | 确认 Pod 未完成初始化，未进入运行或崩溃状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 从指标层面独立印证 Pod 处于等待拉取镜像的状态 |
| 6 | K8s Config | `kubectl get pod` | `resource_limit.memory: 32Mi`, `resource_limit.cpu: 50m` | 排除因资源硬限制导致镜像拉取失败的可能 |
| 7 | K8s Config | `kubectl get pod` | `container.restart_count = 0` | 确认容器尚未启动成功，排除了“先启动后崩溃”的干扰项 |

**证据印证说明：**
K8s 事件事实 #2 直接指出 `lookup registry.invalid ... no such host` 的 DNS 解析错误，解释了镜像拉取失败的机制。事实 #1 和 #3 反映了 kubelet 根据该错误导致的连续重试失败及退避行为。事实 #5 在监控维度上给出了相同的状态映射，而事实 #6、#7 通过资源配置和重启计数排除了内存溢出或启动后崩溃的其他常见原因。所有维度的事实共同指向镜像仓库不可达。

## 🎯 根因分析 · g1

### 因果链

```text
DNS解析失败 (lookup registry.invalid: no such host) → 镜像拉取失败 → 容器启动停滞 → ImagePullBackOff 状态
```

### 根因结论

已确认的根因为：**DNS 解析失败导致镜像仓库不可达**。

Kubelet 在尝试从 `registry.invalid` 拉取镜像 `missing` 时，触发了底层的 TCP 连接失败与 DNS 解析错误（事实 #2）。该网络层面的阻断直接导致 `ImagePullBackOff` 状态（事实 #1、#5）。当前 Pod 处于 Pending 状态且无重启记录（事实 #4、#7），确认了故障始终发生在镜像拉取阶段，而非容器启动后。缺失的日志/Trace 维度（`not_applicable`）符合当前容器未启动的物理状态，不构成对该根因结论的质疑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 22.2s
├─ 并发证据采集: 59.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 59.8s (Evidence 56.2s, RCA 3.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
