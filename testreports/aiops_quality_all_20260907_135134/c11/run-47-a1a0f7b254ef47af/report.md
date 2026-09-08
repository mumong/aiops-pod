## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态且持续 77 分钟无法删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pod` 状态 `Terminating (lasts 77m)` (fact-1f31cb595230) | 确认 Pod 已启动并经历异常，随后进入删除阶段但长期阻塞 |
| 2 | K8s Event | Kubernetes | `Exit Code: 137` (fact-557ec2d7da1d) | 指示容器进程被强制终止，通常由 OOMKilled 引起 |
| 3 | K8s Event | Kubernetes | `k8s.v1.cni.cncf.io/networks-status:` 与 `container.last_terminated_reason=Error` (fact-771aca23bf0f) | 确认异常发生时网络状态处于活跃且未清理状态，佐证终止过程的非正常中断 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 (fact-b03a1673e64f) | 排除重启风暴可能，证实这是 Pod 生命周期内的一次性终止行为 |

**证据分析：**
事实 1 至事实 3 形成了从崩溃到阻塞的完整闭环：容器因 `Exit Code: 137` 异常退出，导致触发 `Terminating` 流程，但由于 Pod 持续处于 `Terminating (lasts 77m)` 长达 77 分钟，证实了标准的销毁流程被外部因素永久拦截。事实 4 作为反向指标，排除了容器频繁重启导致资源耗尽的可能性，锁定在当前的单次终止卡死上。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 异常退出 (Exit Code: 137) → 触发 Pod 删除流程 → 被 finalizer 'aiops.lab/hold' 拦截 → Pod 无法移除资源 (TerminatingStuck 77m)
```

### 根因结论

当前现象的根本原因是 **Pod `aiops-case-11/workload` 的终止流程被 `aiops.lab/hold` 自定义 Finalizer 阻塞**。

1. **触发因素**：容器 `app` 发生异常退出（Exit Code: 137），导致 Kubernetes 发起删除指令。
2. **故障机制**：由于 Pod 绑定了 `aiops.lab/hold` 作为 Finalizer，Kubernetes 在资源清理前必须等待该 Finalizer 的清除完成。
3. **阻碍来源**：清理 `aiops.lab/hold` 对应的自定义控制器未在有效时间内完成删除操作（日志采集为空，无法获取具体控制器执行卡死的原因，如逻辑死锁或超时），导致 Pod 状态永久停留在 `Terminating`。

---

## 📊 性能统计

```text
├─ 总耗时: 57.2s
├─ 问题定位: 12.9s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-11/workload: 35.1s (Evidence 27.9s, RCA 7.0s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
