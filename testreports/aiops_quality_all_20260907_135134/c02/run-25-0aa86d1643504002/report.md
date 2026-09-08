## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，容器 `app` 未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-02/workload-65b7f54794-nqrzv` 状态 Pending，容器 `app` restart_count 为 0 | 确认 Pod 未成功启动，容器进程尚未运行 |
| 2 | K8s Event | Kubernetes | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing"`：`dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 记录最底层错误：域名 `registry.invalid` 解析失败（DNS NXDOMAIN），直接导致拉取中断 |
| 3 | K8s Event | Kubernetes | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认 kubelet 因连续拉取失败已进入退避重试机制，拉取活动停滞 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 从时序监控维度独立证实容器当前正处于镜像拉取退避等待状态 |
| 5 | K8s Config | Kubernetes | 容器 `app` 配置：`resource_request.memory=8Mi`, `resource_limit.memory=32Mi` | 证实内存限制极低，但非本次拉取失败原因 |

**证据印证说明：**
Kubernetes 事件（#2）中的 `no such host` 错误精确解释了 Metrics（#4）中 `ImagePullBackOff` 状态的成因；容器未运行且重启次数为 0（#1）进一步排除了容器内部崩溃或启动后失败的可能，故障完全锁定在镜像拉取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
镜像域名 `registry.invalid` DNS 解析失败 (no such host) → kubelet 请求镜像仓库失败，触发 ErrImagePull 和 ImagePullBackOff → 容器 `app` 处于 Waiting 状态，Pod 维持在 Pending → 应用服务不可用
```

### 根因结论

已确认根因为 **目标镜像域名 `registry.invalid` 无法解析**，导致 kubelet 无法拉取容器镜像。

依据证据 `fact-e5fd6b96b0b5` 中的底层错误 `dial tcp: lookup registry.invalid ... no such host`，结合 `fact-05320a4bc51c` 确认拉取的目标镜像确认为 `registry.invalid/aiops/workload:missing`，故障机制完全由外部镜像仓库的域名可达性异常引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.6s
├─ 并发证据采集: 33.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 33.1s (Evidence 25.8s, RCA 7.2s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
