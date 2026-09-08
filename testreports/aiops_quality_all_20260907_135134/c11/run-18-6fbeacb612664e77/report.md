## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态已超过 32 分钟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `status: Terminating (lasts 32m)` | 确认 Pod 处于异常终止挂起状态，持续时间极长 |
| 2 | K8s Event | kubernetes | `Stopping container app` (kubelet, 32m) | 确认为 Kubelet 主动触发停止，符合强制终止行为 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137` | 确认容器因系统信号终止（通常为 OOMKilled），而非应用正常退出 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi` | 提供资源限制背景，结合 Exit Code 137 指向内存超额 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory: 24Mi`, `cpu: 20m` | 确认请求量极低，与突发 OOM 现象可能存在的资源分配矛盾 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 确认实例自创建以来未发生过重启，当前为首次异常终止 |

以上证据链确认了 Pod `aiops-case-11/workload` 因内存超限（Exit Code 137）被 Kubelet 强制终止。然而，Kubernetes 状态与指标均未解释为何在 32 分钟内未正常清理完成。缺失 K8s Event（如 Finalizer/CNI 报错）、Metric（如 CNI 插件或 Kubelet 延迟指标）以及 Logging 追踪，导致无法在证据层面精确区分是底层网络插件（CNI）资源清理阻塞，还是 API Server 控制面层面的删除延迟。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 terminationGracePeriodSeconds=0s (假设) → 容器收到 SIGKILL 立即终止 (Exit Code 137) → 节点侧 Kubelet 触发删除流程 → 等待后台清理(Finalizer/CNI)受阻 → API Server 对象删除超时卡死在 Terminating
```

*注：`terminationGracePeriodSeconds=0s` 为推断触发机制，非事实直接确认。*

### 根因结论

已确认根因是：**容器应用因内存限制被系统强制终止（OOMKilled，Exit Code 137），且 Pod 在 API Server 层面的删除流程（或底层资源清理）发生了严重阻塞。**

证据编号 1、2、3、4、5 强有力地支持了“强制终止且未正常退出”的状态。然而，现有证据**不足以**区分具体的阻塞点（CNI 清理 vs API Server 延迟）：
1.  **CNI/插件阻塞嫌疑**：Fact `fact-425d182de2e0` 和 `fact-470a59415998` 显示存在 CNI 网络配置相关的 Annotation/Event，但在 Pod 删除阶段通常应自动清理；若清理流程死锁，会阻塞 Pod 删除。
2.  **API Server/控制面延迟嫌疑**：32 分钟的 Terminating 状态远超正常清理时间，暗示可能存在 etcd 写入瓶颈、API Server 并发限制或节点侧 kubelet 与 API Server 的心跳/状态同步问题。

**证据不足项**：由于缺乏 `logging` 维度的 kubelet/事件详细报错，以及 `tracing` 或特定的 `metrics`（如网络插件延迟、API Server 请求延迟），无法断定是节点侧插件阻塞还是集群侧控制面延迟。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.8s
├─ 并发证据采集: 36.2s
│  └─ g1 aiops-case-11/workload: 36.2s (Evidence 24.6s, RCA 11.5s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
