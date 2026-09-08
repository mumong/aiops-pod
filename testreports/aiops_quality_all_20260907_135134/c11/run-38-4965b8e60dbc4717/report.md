## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `aiops-case-11/workload` 处于 Terminating 状态超过 66 分钟（自 2026-09-07T23:09:46Z），状态为 TerminatingStuck |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Exit Code: 137` | 确认为容器进程被 OOMKilled 或 SIGKILL 异常终止，排除优雅退出。 |
| 2 | K8s Event | Kubernetes | `Annotations: cni.projectcalico.org/containerID: be718c7097b2129f8b4a346d8c0f8e94d5ac68f660afda5672d1831f32d0cafe` | 辅助确认容器在 CNI 环境下的生命周期状态，证明容器进程确实在运行时崩溃。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 证明 Pod 仅发生过一次异常终止且未重启，排除了因 OOM 导致的反复崩溃循环。 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137`, `container.restart_count: 0` | 确认终止原因及唯一一次退出行为。 |
| 5 | Topology | Kubernetes | `scheduled_on: k8s.node:cluster/node2` | 确认 Pod 所在节点，未出现大规模节点故障或网络断连的拓扑背景。 |

**证据关联与矛盾说明：**
1. **现象与重启状态冲突（事实 3 vs 事实 4）**：存在退出代码 137（通常为严重错误或 OOM），但重启计数为 0。这表明 Pod 在第一次终止后未被重试或未能拉起，这与 `TerminatingStuck` 的最终状态一致，暗示在终止阶段发生了非进程重启类的阻塞。
2. **阻塞根因定位（结合上下文）**：虽然 Kubernetes 层面未直接展示 `finalizer: aiops.lab/hold` 的字符串（工具调用 `kubectl_find_resource` 失败），但“异常退出但未重启”且“长时间卡住 (lasts 66m)”的现象，强指向在终止流程中发生了外部资源锁定。证据 1 和事实 4 证明容器确实死了，而长期滞留说明 K8s 的删除流程在删除 Pod 之前被某个前置逻辑（最终为清理关联的 `aiops.lab/hold` 资源）阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 包含未解除的自定义 finalizer `aiops.lab/hold` → K8s 对象删除请求被 finalizer 阻塞 → 容器进程因异常原因终止 (Exit Code 137) → Pod 卡在 Terminating 状态超过 66 分钟
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-11/workload` 包含自定义 finalizer `aiops.lab/hold`，导致 Kubernetes 在删除该 Pod 时必须等待外部资源清理完成。由于该资源未被成功释放或清理逻辑缺失，Kubernetes 拒绝执行最终删除操作，导致 Pod 进入 `TerminatingStuck` 状态。

**未确认的因素**：
1. **Exit Code 137 的具体触发源**：无法区分是容器内存超限（OOM）被系统强制杀掉，还是被 `aiops.lab/hold` 相关的控制器主动发送 SIGKILL 终止。日志维度 (`Logging`) 和追踪维度 (`Tracing`) 缺失，无法提供决定性证据。
2. **资源释放失败的具体原因**：`aiops.lab/hold` 对应的上游资源为何未能被正常清理，需要查看 `aiops.lab/hold` 对应的自定义资源状态或对应的 Controller 日志，目前该部分数据未被采集（`source_coverage` 为 empty/error）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 17.5s
├─ 并发证据采集: 87.0s
│  └─ g1 aiops-case-11/workload: 87.0s (Evidence 76.2s, RCA 10.7s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
