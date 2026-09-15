## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Node 'node2' 上 HostPath 卷挂载点 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 缺失或非目录，导致 Pod 'aiops-case-v06/workload' 无法完成卷挂载从而卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount`: hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f468cf25524/input is not a directory | 直接锁定根因：宿主机路径异常 |
| 2 | K8s State | kubelet | `ContainerCreating` (事实 fact-ab197b56062c) | 确认异常状态与原因一致 |
| 3 | K8s Event | kubelet | `Unable to attach or mount volumes... timed out waiting for the condition` (事实 fact-4e468cf25524) | 印证挂载机制长期失效 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 (事实 fact-bc2510f33977) | 外部监控确认容器持续等待挂载 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 (事实 fact-ecfdd1375d97) | 外部监控确认 Pod 卡在 Pending 阶段 |
| 6 | K8s State | kubelet | `pod.condition` Ready=False, ContainersReady=False (事实 fact-d756bcf529a8) | 确认 Pod 核心状态未就绪 |

**证据关联与印证：**
Kubernetes 事件 `fact-1e817f94e4de` 提供了明确的失败机制（hostPath 非目录），解释了 `fact-ab197b56062c` 的 ContainerCreating 状态。Prometheus 指标 `fact-bc2510f33977` 和 `fact-ecfdd1375d97` 从外部视角独立印证了 Pod 卡在等待挂载的状态。日志和 Tracing 因容器无法启动且无 Pod IP，客观上未产生数据，符合“非目录导致无法启动”的预期。

## 🎯 根因分析 · g1

### 因果链

```text
Node 'node2' 文件系统缺失 Pod 所需的 hostPath 目录 (/var/lib/aiops-fixture-unavailable-7f394bef/input) → 
kubelet 执行卷挂载时检测到 hostPath 类型检查失败 → 
Pod 卷挂载持续超时并反复触发 FailedMount 事件 → 
Pod 'aiops-case-v06/workload' 状态卡在 ContainerCreating，容器无法启动
```

### 根因结论

已确认根因为：**Node 'node2' 上 HostPath 卷挂载点 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 缺失或非目录**，导致 Pod 无法完成卷挂载，从而卡在 `ContainerCreating` 状态。

*   **证据支撑**：
    1.  直接失败证据（K8s Event `fact-1e817f94e4de`）：kubelet 明确报告 `hostPath type check failed`。
    2.  现象证据（K8s Event `fact-4e468cf25524`）：挂载操作持续超时。
    3.  状态证据（K8s State `fact-ab197b56062c` & Metric `fact-bc2510f33977`）：Pod 持续处于等待挂载的 `ContainerCreating` 状态。

*   **缺失事实**：
    无法确定该目录实际缺失的具体原因（如节点故障、清理脚本错误或配置错误），但这不影响对当前 Pod 故障的直接归因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.4s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-v06/workload: 40.4s (Evidence 30.3s, RCA 9.7s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error, pod-sandbox-create-failed
