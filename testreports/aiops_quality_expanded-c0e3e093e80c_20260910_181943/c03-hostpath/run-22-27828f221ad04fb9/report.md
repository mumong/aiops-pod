## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload 处于 ContainerCreating 状态无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v06/workload` 状态为 `ContainerCreating` | 确认 Pod 处于启动前的挂起等待状态，未进入 Running 阶段 |
| 2 | K8s Event | kubernetes | `FailedMount`: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接指向卷挂载失败的确切原因：目标路径不存在或非目录，是根本故障源 |
| 3 | K8s Event | kubernetes | `FailedMount`: `timed out waiting for the condition` (x23 over 34m) | 证实挂载失败具有持续性，导致 Pod 长时间无法启动 |
| 4 | K8s Config | kubernetes | Volume `input` 挂载至容器 `app`；资源配置 `CPU 50m/5m, Memory 32Mi/8Mi` | 提供上下文，排除资源配额或计算资源不足导致的调度/启动失败 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 1 | 独立验证 Pod 当前确实处于 `ContainerCreating` 等待状态，与 K8s State 一致 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"}` 值为 0 | 证实容器未发生过启动或重启尝试，处于持续排队等待中 |

**证据综合：**
Kubernetes 事件明确记录了挂载失败的具体错误（`hostPath type check failed`），这是定位故障的唯一决定性事实。K8s State 中的 `ContainerCreating` 状态以及 Prometheus 监控中的等待原因为“Pod 卡在启动阶段”提供了跨维度的一致性印证。配置与指标数据排除了资源瓶颈作为触发因素的可能。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 缺少指定目录 (/var/lib/aiops-fixture-unavailable-7f394bef/input) → kubelet 执行 Volume.SetUp 触发类型检查失败 → 卷 `input` 挂载持续失败 → Pod 停滞在 ContainerCreating 状态
```

### 根因结论

**已确认的根因：** Pod `aiops-case-v06/workload` 挂载的 HostPath 卷在节点 `node2` 上找不到预期的目录结构。

证据 `fact-45550a323619` 中记录的 `hostPath type check failed` 错误直接证实了这一点：kubelet 在尝试挂载 `input` 卷时，发现路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 并非有效目录。这一环境配置缺失导致挂载操作持续失败（证据 3），进而阻塞了容器启动流程，表现为 Pod 长期处于 `ContainerCreating` 状态（证据 1、证据 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 37.3s
├─ 并发证据采集: 41.6s
│  └─ g1 aiops-case-v06/workload: 41.6s (Evidence 32.0s, RCA 9.5s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-config-error, pod-volume-mount-failed, pod-sandbox-create-failed
