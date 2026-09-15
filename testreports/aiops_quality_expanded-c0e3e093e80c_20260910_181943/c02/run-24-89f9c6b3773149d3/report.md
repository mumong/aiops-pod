## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，容器 `app` 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason="ImagePullBackOff"` | 确认 Pod 容器 `app` 当前终止于拉取镜像的失败状态 |
| 2 | K8s State | kubernetes | `pod.phase="Pending"`, `restart_count=0` | 确认 Pod 调度成功但因无法拉取镜像始终处于挂起状态，且未发生过有效启动 |
| 3 | K8s Event | kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 反映 kubelet 正在进行指数退避重试，直接印证了拉取动作的持续失败 |
| 4 | K8s Event | kubernetes | `Failed ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供底层根本原因：DNS 解析失败，确认为镜像地址配置错误而非网络连通性问题 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}=1` | 独立指标源验证了 Kubernetes API 报告的等待状态 |

Kubernetes 事件明确指出了失败的根本原因是 DNS 解析失败（`no such host`），这与 `ImagePullBackOff` 的状态和指标高度一致。由于容器始终未能启动，日志和链路追踪维度无业务数据产出，当前事实已足以闭环验证根因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 registry.invalid 的镜像地址 → kubelet 执行 PullImage 时 DNS 解析失败 (no such host) → 镜像拉取失败并触发指数退避 (Back-off) → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因是：**镜像仓库配置错误**。

Pod 配置了不可达的镜像地址 `registry.invalid/aiops/workload:missing`，导致 kubelet 在尝试拉取镜像时，底层 DNS 解析查询失败（见证据 #4 `no such host`）。由于镜像始终无法获取，kubelet 按照退避策略反复重试（见证据 #3），最终导致容器处于 `ImagePullBackOff` 状态，Pod 保持 `Pending`（见证据 #1、#2）。该结论由 Kubernetes API 事实与 Prometheus 指标相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 59.0s
├─ 问题定位: 16.2s
├─ 并发证据采集: 34.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 34.6s (Evidence 26.6s, RCA 7.9s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
