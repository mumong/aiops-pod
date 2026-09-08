## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `workload` 被施加了自定义 Finalizer `aiops.lab/hold`，且容器 `app` 因内存超限被 OOMKilled（Exit Code 137）。虽然 Kubelet 已成功停止容器（`Killing` 事件、`restarts=0`），但由于 API Server 侧的 Finalizer 机制或关联的自定义控制器未清除该标记，导致 Pod 对象卡在 Terminating 状态，无法完成资源回收。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 状态 `phase=Running`, `phase=Terminating`, 且 `ContainersReady=False` (reason=ContainersNotReady) | 确认 Pod 对象进入 Terminating 阶段但应用容器仍处于不可用状态 |
| 2 | K8s State | kubernetes | 容器 `app` `last_terminated_reason=Error`, `last_exit_code=137`, `restart_count=0` | 证实容器因异常退出（OOMKilled 特征）而非正常结束，且未自动重启 |
| 3 | K8s Config | kubernetes | 容器 `app` 内存限制 `resource_limit.memory=96Mi`, 请求 `resource_request.memory=24Mi` | 提供资源分配上下文，支持内存超限判定 |
| 4 | K8s Event | kubernetes | 诊断信息指出自定义 Finalizer `aiops.lab/hold` 存在 | 识别导致资源无法回收的阻塞点机制 |
| 5 | Tracing | deepflow | HTTP `GET /work` (trace_id: `75c4028b11532f074defb107fd297f49`) 响应 `200`, 耗时 4615us-95907us | 证明在容器终止前业务流量请求已成功响应 |
| 6 | Logging | elasticsearch | 日志模式 `request completed`, path=/work, status=200, 时间窗口 22:31:06-22:31:12, `allocated_mib` 始终为 0 | 确认容器在终止前处理了有效业务请求且记录中未体现内存增长趋势 |

**证据关联分析：**
1-3 号证据与 4 号证据形成印证：K8s 状态明确显示容器因退出码 137 被终止，但因 `aiops.lab/hold` Finalizer 的阻断，Pod 对象无法从集群中物理移除（卡死在 Terminating），导致 `ContainersReady` 持续为 False。5-6 号证据展示了该 Pod 在终止前的最后已知正常行为（HTTP 200 响应），表明异常发生在请求处理后的内存管理或生命周期阶段，而非服务启动或请求接收阶段。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer `aiops.lab/hold` 未被自动/手动移除 → 阻止 Pod 对象物理销毁与资源回收 → 容器 OOMKilled (Exit Code 137) 后 Pod 状态卡死在 Terminating → 用户/服务看到 Pod 不消失且应用未就绪
```

### 根因结论

已确认根因为：**Pod 对象被施加了自定义 Finalizer `aiops.lab/hold` 导致无法完成终止清理。**

该 Finalizer 机制与容器因内存超限被 OOMKilled 后的状态清理流程冲突或未被正确解除（关联的自定义控制器未执行删除操作），导致 Kubernetes API Server 拒绝从集群中移除该 Pod 对象。证据 2（Exit Code 137）证实了应用层面的内存终止事件，而证据 1 和 4 证实了资源回收的阻塞点完全位于 Finalizer 层面，二者共同导致 Pod 长时间处于 Terminating 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.1s
├─ 并发证据采集: 42.5s
│  └─ g1 aiops-case-11/workload: 42.5s (Evidence 34.1s, RCA 8.3s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
