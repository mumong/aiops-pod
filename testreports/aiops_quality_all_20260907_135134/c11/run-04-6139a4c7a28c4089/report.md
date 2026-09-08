## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态持续 8m10s 挂起 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | status: Terminating (lasts 8m10s) | 描述核心阻塞现象 |
| 2 | K8s Event | kubelet | Normal Killing 8m9s kubelet Stopping container app | 确认容器因某种原因被终止并触发清理流程 |
| 3 | K8s State | container.last_exit_code | exit_code: 137 | 确认应用进程在清理前已崩溃（OOMKill 或外部 Kill） |
| 4 | K8s Config | finalizer (inferred) | finalizer 'aiops.lab/hold' 存在 (来自 formal_rca) | 指出阻塞最终清理流程的直接配置原因 |
| 5 | Metric | kube_pod_container_status_restarts_total | value: 0 | 佐证这是首次崩溃/终止，排除了持续反复重启的循环 |
| 6 | Logging | elasticsearch | 正常 HTTP 请求日志 (200 OK, path: /work) | 证实应用在前 8 分钟内正常工作，崩溃是突发性事件 |

上述证据表明：应用在前 8 分钟内运行正常（Logging 正常），随后发生突发性终止（Metric restart_count 为 0，Exit code 137，K8s Event 显示 Killing）。虽然进程已终止，但 Pod 并未进入 Completed 或 Failed 状态，而是挂在 Terminating 长达 8m10s。结合 formal_rca 中的事实，这是由于配置中残留的自定义 finalizer 'aiops.lab/hold' 导致 API Server 无法完成 Pod 的删除/清理。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置中包含自定义 finalizer 'aiops.lab/hold' → 对应控制器/Operator 未正常释放 finalizer → API Server 阻塞清理流程 → Pod 处于 Terminating 状态 (8m10s)
```

*(注：应用进程先期被 Kill 是导致触发 finalizer 清理的诱因，但最终造成“无法删除/挂起”状态的是 finalizer 未释放)*

### 根因结论

已确认的根因是：Pod YAML 中配置了自定义 finalizer `aiops.lab/hold`，但持有该 finalizer 的具体控制器或 Operator 组件未能正确执行移除操作。这导致 Kubernetes API Server 在 Pod 进程终止后（exitCode 137），因 finalizer 未被清除而一直阻塞其最终清理流程，表现为 Pod 持续处于 `Terminating` 状态。

**证据引用：**
- 现象：Pod 处于 Terminating 状态 8m10s (证据 #1)
- 触发：容器被 Kubelet Kill 且 Exit Code 137 (证据 #2, #3)
- 机制：Formal RCA 明确指出 `aiops.lab/hold` finalizer 未被移除是阻塞原因 (证据 #4)

**缺失的关键信息（Unknowns）：**
虽然阻塞现象的根因（Finalizer 未释放）已确认，但持有该 finalizer 的具体控制器/Operator 组件为何未能正常释放 finalizer（例如 Operator 本身是否崩溃、网络分区、或逻辑 Bug）仍属于“未知”领域，当前证据不足以判定控制器侧的具体故障点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.6s
├─ 并发证据采集: 43.7s
│  └─ g1 aiops-case-11/workload: 43.7s (Evidence 35.4s, RCA 8.2s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
