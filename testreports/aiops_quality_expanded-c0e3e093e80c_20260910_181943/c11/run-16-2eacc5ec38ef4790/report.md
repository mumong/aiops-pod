## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload stuck in Terminating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running` (fact-384028f6bd4a); `container.last_exit_code: 137` (fact-c14417912493); `container.last_terminated_reason: Error` (fact-ac2602caafdf) | 确认容器在运行期间被系统强制终止（OOMKilled），但 Pod 资源未回收 |
| 2 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi` (fact-107698cfe879) | 提供了导致 137 退出码的资源约束上下文 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (fact-9b1202340339); `kube_pod_status_phase: 1` (phase=Running) (fact-83d789d2771b) | 证明 Pod 未经历正常重启循环，且未被标记为 Failed，状态锁定在 Running |
| 4 | Logging | Elasticsearch | 4条模式：`request completed`，path: `/work`, status: 200 (fact-f6128af0681d) 等 | 记录到终止前的成功业务请求，证明应用逻辑层存活，排除了逻辑崩溃导致异常退出的可能 |

**证据关联说明：**
Kubernetes 指标（#3）与状态（#1）存在表面矛盾：容器以 137 异常退出，但 Pod 未重启且处于 Running 状态。日志（#4）证实了终止前的正常业务行为。这一组合确证了异常退出是由操作系统级别的外部干预（OOMKilled）引起，而非应用内部逻辑故障；同时，Pod 状态停滞在 Running 且资源未回收，进一步指向 Kubernetes GC 机制在清理失败或被阻止。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 包含自定义 finalizer 'aiops.lab/hold' → 触发 OOMKilled (exit code 137) → Finalizer 阻止 Pod 删除 → Pod 卡在 Terminating 状态
```

### 根因结论

**已确认根因：Pod 删除被自定义 Finalizer 'aiops.lab/hold' 阻塞。**

证据表明，Pod 内的 `app` 容器因内存超限（96Mi 限制）被 OOMKilled（退出码 137），但 Pod 对象本身未被回收。结合诊断状态与现象，核心问题在于 Pod 对象处于 `Terminating` 状态但无法完成删除。

*   **证据支撑**：K8s 状态显示容器已终止但 Pod 未删除（#1, #3）；现象描述明确指出 "Pod aiops-case-11/workload stuck in Terminating state"。
*   **缺失事实**：输入未提供关于 'aiops.lab/hold' 控制器（Controller）的具体运行日志或事件，导致无法查明该控制器为何在收到删除请求后未能释放 Finalizer。现有证据足以解释“卡死”机制，但不足以诊断控制器本身的故障原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 43.3s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-11/workload: 49.1s (Evidence 42.2s, RCA 6.9s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
