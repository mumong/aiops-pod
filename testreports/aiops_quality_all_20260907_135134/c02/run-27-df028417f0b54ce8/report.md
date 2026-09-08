## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | 镜像仓库域名 registry.invalid 无法通过 DNS 解析（no such host），导致容器镜像拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: ImagePullBackOff` (repeated) | 确认镜像拉取失败已进入重试/退避阶段 |
| 2 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... failed to do request: Head "https://registry.invalid/v2/...": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供确切的 DNS 解析失败错误信息，直接指向域名不可达 |
| 3 | K8s State | kubernetes | `pod.status: Pending`, `container.restart_count: 0` | 证实 Pod 仍处于等待状态，尚未启动成功 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (`container=app`, `reason=ImagePullBackOff`): `1` | 独立量化确认当前处于 ImagePullBackOff 等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` (`container=app`): `0` | 排除因 CrashLoopBackOff 等应用错误导致的反复重启，确认问题停留在启动前阶段 |

**证据说明**：
Kubernetes 事件（#1, #2）明确记录了镜像拉取失败的根本原因是 `registry.invalid` 域名无法通过 DNS 解析 (`no such host`)。Kubernetes 状态（#3）和 Prometheus 指标（#4, #5）相互印证，表明 Pod 自始至终未能成功启动（重启次数为 0），且目前仍处于因镜像拉取失败而导致的 `Pending` 和 `ImagePullBackOff` 状态，未发现其他异常维度（如 OOM 或 Crash）。

## 🎯 根因分析 · g1

### 因果链

```text
DNS 解析失败 (lookup registry.invalid ... no such host) → 镜像拉取拒绝 (Head request failed) → 镜像拉取回退 (ImagePullBackOff) → Pod 处于 Pending 状态，业务不可用
```

### 根因结论

已确认根因为**镜像仓库域名不可达**。
集群中的 DNS 服务无法解析目标镜像仓库域名 `registry.invalid`，导致 Kubernetes 调度器或 kubelet 在执行拉取操作时底层网络请求失败（`dial tcp: lookup ... no such host`），进而引发 `ErrImagePull` 并最终进入 `ImagePullBackOff` 等待状态 [证据 #2]。该结论得到了 Pod 状态 [证据 #3] 及等待原因指标 [证据 #4] 的交叉验证。

---

## 📊 性能统计

```text
├─ 总耗时: 51.6s
├─ 问题定位: 15.5s
├─ 并发证据采集: 27.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 27.2s (Evidence 22.3s, RCA 4.7s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
