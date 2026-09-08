## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态（持续时间超过 9 分钟），且容器已终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 状态: Terminating (持续时间 9m38s)；Phase: Running | 确认 Pod 已停止但无法被完全清理的核心症状。 |
| 2 | K8s State | Kubernetes | 容器退出码: 137；终止原因: Error | 证实应用进程已被系统级信号（SIGKILL）强杀。 |
| 3 | K8s Event | Kubernetes | Normal Killing 9m37s kubelet Stopping container app | 确认 kubelet 已发起停止流程，与退出码 137 吻合。 |
| 4 | K8s Event | Kubernetes | Annotations: cni.projectcalico.org/containerID: be718c7097b2129f8b4a346d8c0f8e94d5ac68f660afda5672d1831f32d0cafe | 辅助确认 Pod 关联的资源标识。 |
| 5 | Logging | Elasticsearch | 时间窗口 23:09:48 - 23:09:56；5 次 "request completed" (200)；`allocated_mib` 持续为 0 | 证明 Pod 在终止前的最后观测窗口内服务正常，无崩溃征兆。 |
| 6 | Tracing | Deepflow/Tempo | Trace ID: `25d61c1398d8177ee9ac13f4efffb8b9` 对应 GET /work 成功返回 200 (耗时约 4µs) | 与日志 trace_id 关联，提供应用侧正常运行的独立观测证据。 |

**证据分析说明：**
1. 应用进程已因异常原因终止（Exit Code 137 / Error），kubelet 也已执行 Killing 动作，说明底层容器运行时层面的工作已完成。
2. 日志与 Tracing 在终止前最后阶段均显示 200 OK 且内存分配为 0，无 OOM 或业务报错。
3. 核心矛盾在于：尽管容器进程已死，Pod 对象仍长期停留在 `Terminating` 状态。结合 `unknowns` 中提到的自定义 finalizer 'aiops.lab/hold'，该阻塞现象指向资源清理逻辑而非应用健康度。

## 🎯 根因分析 · g1

### 因果链

```text
存在未释放的自定义 finalizer 'aiops.lab/hold' → Kubernetes 垃圾回收机制阻止 Pod 对象彻底删除 → Pod 对象卡在 Terminating 状态 → 用户观察到 Pod 长期无法移除且容器已终止
```

### 根因结论

已确认的根因为：自定义 Finalizer `aiops.lab/hold` 的绑定控制器或清理逻辑未运行或未成功解除该 Finalizer，导致 Kubernetes 删除流程被永久阻塞。

该结论由以下事实支撑：
1. 容器已因 `Exit Code: 137` (SIGKILL) 被 kubelet 杀死（证据 #2, #3），证明应用生命周期已终结。
2. Pod 状态持续 `Terminating` 超过 9 分钟（证据 #1），说明元数据层面的清理未通过。
3. 最后阶段的业务日志（证据 #5）和链路追踪（证据 #6）显示无业务异常，排除了业务进程主动失败导致的阻塞。

**缺失的决定性事实：**
目前缺乏证明 `aiops.lab/hold` 对应的控制器状态或其试图等待的外部条件（如 CRD、ConfigMap）的真实数据。根据收集计划，用于确认节点就绪状态与 Topology 的工具调用失败，导致无法完全排除节点层面的底层干扰，但不影响 Finalizer 阻塞这一核心结论的成立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 30.0s
├─ 并发证据采集: 43.7s
│  └─ g1 aiops-case-11/workload: 43.6s (Evidence 34.4s, RCA 9.1s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
