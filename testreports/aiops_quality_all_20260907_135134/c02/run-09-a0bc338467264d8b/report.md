## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，容器 app 未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-02/workload-65b7f54794-nqrzv` 状态为 Pending | 确认异常实体及其生命周期阶段 |
| 2 | K8s Event | Kubernetes | `Error: ErrImagePull` | 触发异常的直接原因（镜像拉取失败） |
| 3 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明异常根源在于 DNS 解析失败，域名无效 |
| 4 | K8s Event | Kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认系统正在因持续拉取失败而进入退避机制 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=ImagePullBackOff, value=1) | 指标验证了 Pod 处于等待/回退状态的事实 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (value=0) | 证明容器从未成功启动过，排除了运行时 OOM 等导致重启的因素 |

**证据关联说明：**
K8s Event 3 中的 `no such host` 错误明确指出了 `registry.invalid` 域名无法解析，这直接导致 Event 2 的 `ErrImagePull` 和 Event 4 的 `BackOff`。Metric 5 从监控层面印证了 Pod 处于 `ImagePullBackOff` 状态，而 Metric 6 确认了该容器是首次拉取即失败，尚未运行过。所有证据均指向同一个故障路径：无法解析镜像仓库域名。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像配置使用了无效域名 registry.invalid → kubelet 尝试解析域名失败 (DNS NXDOMAIN) → 镜像拉取直接失败并触发 BackOff 机制 → Pod 卡在 Pending 状态 (ImagePullBackOff)
```

### 根因结论

已确认根因：**Pod 配置使用了不可解析的无效镜像域名 `registry.invalid`**。

该配置导致 kubelet 在执行镜像拉取时，DNS 系统返回 `no such host` (fact-3)，引发镜像拉取请求持续失败 (fact-2)。系统随后进入指数退避拉取模式 (fact-4, fact-5)，致使 Pod 状态被锁定在 `ImagePullBackOff` (fact-1, fact-5)。Metric 数据表明容器自始未成功启动 (fact-6)，彻底排除了应用逻辑或资源争用作为故障主因的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 59.6s
├─ 问题定位: 20.2s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 30.2s (Evidence 22.3s, RCA 7.7s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
