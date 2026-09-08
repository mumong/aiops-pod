## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 存在自定义 finalizer 'aiops.lab/hold'，其清理逻辑未执行或挂起，导致 Pod 的 deletionTimestamp 过期后仍无法从集群中移除，尽管容器已因 SIGKILL (Exit Code 137) 终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `Terminating (lasts 55m)` | 确认 Pod 处于长期挂起状态 |
| 2 | K8s Event | event.message | `Normal Killing         55m   kubelet            Stopping container app` | 记录容器终止行为发生的时间点 |
| 3 | K8s State | container.last_exit_code | `exit_code: 137` | 确认容器因 SIGKILL 异常退出 |
| 4 | K8s State | pod.condition | `ContainersReady: False (ContainersNotReady: [app])` | 确认容器未恢复健康，处于不就绪状态 |

Pod 状态已持续 `Terminating` 55 分钟，表明删除流程卡死。尽管 kubelet 在 55 分钟前发送了 `Stopping container app` 事件，且容器随后以 `Exit Code 137` 终止，但 Pod 仍处于 `ContainersNotReady` 且 `phase` 未清理的挂起状态，说明 Kubernetes 的删除预检查机制被阻断。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 清理逻辑未执行/挂起 → 阻断 Pod 删除预检查 → 容器正常退出但 Pod 拒绝从 API Server 移除 → Pod 长期处于 Terminating 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-11/workload` 存在自定义 finalizer `aiops.lab/hold`。该 finalizer 对应的清理逻辑（如外部系统回调、依赖资源释放等）未能正常执行或处于挂起状态，导致 Kubernetes API Server 在删除 Pod 时无法完成预检查，从而将 Pod 锁定在 `Terminating` 状态。证据显示容器进程已因资源限制或外部信号被强制终止（Exit 137），但 Pod 资源的最终清理阶段被阻塞，形成“僵尸”Pod 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 54.9s
├─ 问题定位: 15.8s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-11/workload: 32.0s (Evidence 25.0s, RCA 6.9s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
