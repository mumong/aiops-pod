## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，持续 73 分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes (Pod) | `status: Pending` (`fact-00e3d08d77f4`) | 确认 Pod 处于不可运行状态，无法启动应用容器 |
| 2 | K8s Event | Kubernetes (kubelet) | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (`fact-2e52ec17e4c0`) | 直接指出失败的镜像仓库地址，表明拉取操作被拒绝并进入退避 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, reason=`ImagePullBackOff` (`fact-e20a38dd41e4`) | 独立于 Event 确认了容器当前等待的具体原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (`fact-3b211b1e8ace`) | 确认容器从未成功启动，排除了启动后崩溃导致重启的可能性 |

**证据分析：**
Kubernetes Event 提供了最核心的错误细节，明确指向镜像地址 `registry.invalid/aiops/workload:missing` 是拉取失败的直接原因。Prometheus 监控数据（#3, #4）从状态指标层面独立印证了 `ImagePullBackOff` 这一异常原因，且容器重启次数为 0 佐证了 Pod 始终处于初始拉取阶段，未进入应用运行周期。日志与追踪维度因 Pod 未启动及工具受限不可用，但不影响此核心事实链。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库配置无效('registry.invalid/aiops/workload:missing') → kubelet 拉取镜像失败触发 BackOff → Pod 进入 ImagePullBackOff/Pending 状态 → 应用容器无法启动，无日志产生
```

### 根因结论

已确认的根因为 **容器镜像配置错误**。

Pod `aiops-case-02/workload-65b7f54794-rnlv4` 在启动过程中指定了无法访问或无效的镜像仓库地址 `registry.invalid/aiops/workload:missing`。这导致 kubelet 无法拉取容器镜像，进而持续失败并触发 BackOff 机制，最终使 Pod 长期处于 `ImagePullBackOff` 和 `Pending` 状态。该故障由 Kubernetes 事件（#2）和等待原因指标（#3）共同证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 28.8s
├─ 并发证据采集: 54.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 54.4s (Evidence 46.4s, RCA 7.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
