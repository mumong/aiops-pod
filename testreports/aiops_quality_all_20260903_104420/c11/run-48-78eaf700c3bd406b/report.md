## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态，且被 `aiops.lab/hold` finalizer 阻滞（TerminatingStuck）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态 `Terminating` 持续 `88m`；条件 `ContainersNotReady` 且 `status=False` | 证实故障长期存在，Pod 资源释放受阻 |
| 2 | K8s State | Kubernetes | 容器 `app` 上次终止原因 `Error`，退出码 `137` | 证实 Pod 经历了非预期终止，是阻滞前的最后一次状态变化 |
| 3 | K8s Config | Kubernetes | 配置了自定义 finalizer `aiops.lab/hold` | 直接定位阻滞根源：Kubernetes 在清理资源前必须等待该标识被移除 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 当前值 `3297280` bytes (约 3.1 MiB) | 证实容器仍有残余内存占用（配置上限 96Mi），侧面反映进程或 finalizer 逻辑未完全退出 |
| 5 | Logging | Elasticsearch | 日志模式 `request completed` 最后记录于 `2026-09-03T22:31:12.134Z`，后续窗口无业务日志 | 证实应用业务层在异常退出前已正常结束请求，故障发生在更底层 |
| 6 | Tracing | Tempo | Trace ID `75c4028b11532f074defb107fd297f49` 显示 `GET /work` 返回 `200` | 与日志一致，证实终止前最后一次流量处理成功，未报 HTTP 错误 |

**证据关联说明**：
Kubernetes 的 `Terminating` 状态（#1）结合 `aiops.lab/hold` Finalizer（#3）确立了阻滞的直接原因。容器退出码 `137`（#2）与内存残留（#4）表明 Pod 在异常终止后未能通过 Finalizer 逻辑实现资源回收或状态清理。追踪（#6）与日志（#5）确认在异常发生前业务请求本身是正常的，排除了应用层逻辑导致 Finalizer 阻滞的可能，进一步指向 Finalizer 自身的实现或绑定问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被请求删除 → Custom Finalizer 'aiops.lab/hold' 未被清除 → Kubernetes 阻止资源清理 → Pod 持续处于 Terminating 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-11/workload` 被自定义 finalizer `aiops.lab/hold` 阻滞，导致无法从 `Terminating` 状态过渡到 `Deleted`。
*   **证据支撑**：Kubernetes 状态显示 `Terminating` 持续 88 分钟（证据 #1），且明确配置了 `aiops.lab/hold` finalizer（证据 #3）。Kubernetes 机制规定在 finalizer 移除前不得删除对象，这是导致阻滞的直接原因。
*   **前序状态**：容器以退出码 `137` 异常终止（证据 #2），但 finalizer 机制未能完成清理工作，使得 Pod 卡在 Terminating 阶段。

**未确认/证据不足的环节**：
*   **阻滞的具体内部原因**：现有日志（#5）和追踪（#6）仅显示业务层正常结束，无法确认 `aiops.lab/hold` 对应的 Controller 或 Operator 在处理该 finalizer 时是否报错或超时。
*   **退出码 137 的触发源**：虽然 `exitCode 137` 通常暗示 OOM Killer 或信号中断，但无法从现有事实中确认是 Kubelet OOM、Probe 失败还是 Finalizer 进程行为直接触发了此次终止。

---

## 📊 性能统计

```text
├─ 总耗时: 11.3m
├─ 问题定位: 16.2s
├─ 并发证据采集: 648.2s
│  └─ g1 aiops-case-11/workload: 648.2s (Evidence 638.5s, RCA 9.6s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
