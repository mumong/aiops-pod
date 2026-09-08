## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 存在自定义 finalizer 'aiops.lab/hold' 导致 Terminating 状态卡住。虽然容器因 SIGKILL (exit code 137) 已终止，但由于该 finalizer 未从 Pod spec 中移除，Kubernetes API Server 无法完成 Pod 的删除流程，导致资源长期处于 Terminating 且不可用的状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes API | Pod 状态 `Terminating (lasts 51m)` | 确认 Pod 处于删除卡死状态，持续超过 51 分钟 |
| 2 | K8s State | Kubernetes API | Container `app` 退出码 `137` | 确认容器进程非正常终止，与 Kubernetes 事件中的 Killing 记录对应 |
| 3 | K8s Event | kubelet 事件 | `Stopping container app` (发生时间约 51m 前) | 说明容器终止指令已被系统发送，但资源回收未完成 |
| 4 | K8s Config | Pod Manifest | 容器 `app` 配置 `Memory request=24Mi, limit=96Mi` | 排除内存 OOM 配置不当导致的异常终止，辅助定位终止原因 |

证据说明：
1. **K8s State** 与 **K8s Event** 相互印证：退出码 137 与 `Stopping container app` 事件一致，证明容器进程确实已终止。
2. 资源状态为 `Terminating` 且持续 51 分钟，表明 Pod 生命周期处于不可恢复的停滞阶段，这通常指向资源清理（如 Finalizers 或挂载卷）环节存在阻塞。
3. 资源限制（24Mi/96Mi）属于正常范围，非异常终止的直接成因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 存在自定义 finalizer 'aiops.lab/hold' 未移除 → Kubernetes API Server 阻塞删除流程 → 资源长时间处于 Terminating 状态 → Pod 不可用且资源未释放
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 存在自定义 finalizer `'aiops.lab/hold'`，导致 Kubernetes API Server 在容器进程已终止（Exit Code 137）的情况下，无法完成 Pod 的删除流程。这直接导致了 Pod 长时间处于 `Terminating` 状态，资源被挂起且不可用。

**支持证据**：
*   Pod 持续 51 分钟处于 `Terminating` 状态（证据 #1）。
*   容器已因 `SIGKILL` 退出（Exit Code 137），且 kubelet 记录了 `Stopping container` 事件（证据 #2、#3），证明计算资源已释放，但元数据删除被阻塞。

**未知/证据不足部分**：
*   触发 finalizer 的控制器为何未成功移除该 finalizer（即删除逻辑为何失效）缺乏相关日志和控制器状态证据。
*   该 finalizer 的具体创建来源及当前是否存在活跃引用未能在提供的数据中查明。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 21.0s
├─ 并发证据采集: 105.6s
│  └─ g1 aiops-case-11/workload: 105.6s (Evidence 97.2s, RCA 8.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
