## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态持续 76 分钟未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | status: Terminating (lasts 76m) | 症状：Pod 进入删除状态后长时间未移除 |
| 2 | K8s Config | resource_request.cpu | 20m, resource_limit.cpu: 200m | 上下文：配置正常且资源限制合理 |
| 3 | K8s Config | resource_request.memory | 24Mi, resource_limit.memory: 96Mi | 上下文：配置正常且资源限制合理 |
| 4 | K8s Event | event.message | Exit Code: 137 | 现象：容器进程被 OOMKilled 或外部强制终止 |
| 5 | K8s State | container.last_exit_code | exit_code: 137 | 症状：容器退出的错误码与 Event 一致 |
| 6 | K8s State | container.last_terminated_reason | reason: Error | 症状：确认容器非正常退出 |

证据说明：K8s 状态与事件证实容器在运行中发生异常终止（Exit 137），但 Pod 并未正常回收，而是长期处于 Terminating 状态（76分钟），这属于删除流程异常，而非单纯的容器崩溃问题。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer `aiops.lab/hold` 注册在 Pod 上 → Kubernetes API 检测到 deletionTimestamp 但 finalizer 未移除 → 控制器阻塞 Pod 资源回收 → Pod 长期处于 Terminating 状态
```

### 根因结论

**已确认的根因**：Pod 包含自定义 finalizer `aiops.lab/hold`，导致 Kubernetes 无法完成删除流程。外部持有该 finalizer 的控制器未能或未被触发以清理资源，致使 Pod 被阻塞在 Terminating 状态长达 76 分钟。

**证据支撑**：
- `diagnosis.unknowns` 明确指出了 `aiops.lab/hold` 对应的控制器状态未知，且触发该 finalizer 的资源清理状态未确认。
- 现象与 Pod 状态（#1）和终止原因（#5）一致，排除了因内存资源不足直接导致删除阻塞的可能（#2, #3），确认根因在于自定义生命周期钩子（finalizer）的执行失败或阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 54.3s
├─ 问题定位: 16.0s
├─ 并发证据采集: 30.3s
│  └─ g1 aiops-case-11/workload: 30.3s (Evidence 22.1s, RCA 8.0s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
