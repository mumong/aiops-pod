## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | Pod status: `Pending`; Pod phase: `Pending` | 确认容器未启动，处于等待调度后状态 |
| 2 | K8s Event | K8s Event | `Error: ErrImagePull` (x4), `Error: ImagePullBackOff` (x6), `Back-off pulling image "registry.invalid/aiops/workload:missing"` (x21) | 明确指示镜像拉取持续失败，且已进入指数退避阶段 |
| 3 | K8s Event | K8s Event | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (x4 over 5m17s) | 给出致命原因：DNS 解析完全失败，无法访问目标域名 |
| 4 | Metric | Metrics | `kube_pod_container_status_waiting_reason` (reason: `ImagePullBackOff`, value: `1`) | 独立观测到容器状态确认为拉取失败 |

当前集群中 Pod `aiops-case-02/workload-65b7f54794-jmq6b` 持续处于 `Pending` 和 `ImagePullBackOff` 状态。Kubernetes Events 明确记录了由于 `registry.invalid` 域名解析失败（`no such host`），导致 kubelet 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时连续报错（ErrImagePull 和 ImagePullBackOff），Metrics 也同步确认了该等待状态。日志与 Trace 因容器未启动而未生成，现有事实已完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了无效域名 registry.invalid → DNS 解析失败 (no such host) → kubelet 拉取镜像被拒绝 → 容器持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因为：**Pod 规范中配置的镜像地址 `registry.invalid/aiops/workload:missing` 包含无效的域名 `registry.invalid`**。

这一配置错误导致 kubelet 在尝试连接镜像仓库时，底层网络请求因 DNS 解析失败（`lookup registry.invalid ... no such host`）而被拒绝（证据 #3、#4）。由于镜像始终无法拉取，容器无法启动，从而引发了集群中该 Pod 持续的 `ImagePullBackOff` 状态（证据 #2、#3）。现有证据充分支持该结论，无需补充。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.7s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 41.4s (Evidence 32.7s, RCA 8.6s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
