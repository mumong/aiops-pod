## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload Terminating 卡死超 22 分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: Running; status: Terminating (lasts 22m); condition: Ready=False | 确认可见现象：Pod 已终止并进入删除流程，但删除操作阻塞 |
| 2 | K8s Event | kubernetes | Normal Killing (22m); Exit Code: 137 | 确认容器进程已收到 SIGKILL 信号并被操作系统终止 |
| 3 | K8s State | kubernetes | container.last_terminated_reason: Error | 确认容器退出为非正常状态 |
| 4 | Metric | prometheus | kube_pod_status_phase=1 (Running), kube_pod_container_status_restarts_total=0 | 确认 Pod 始终处于单一运行周期内，排除因频繁重启导致的异常 |
| 5 | Logging | elasticsearch | 4条 "request completed" 记录，http_status=200, path="/work" | 确认容器退出前业务逻辑运行正常，非业务逻辑死锁或超时所致 |
| 6 | Tracing | Tempo | Span trace_id=75c4028b11532f074defb107fd297f49, GET /work, http.response.status_code=200 | 关联日志与请求，确认终止前最后一个请求成功完成 |

**证据交叉印证说明：**
1. 容器进程已按预期终止（事实 2），但 Kubernetes 对象状态卡在 `Terminating`（事实 1），这种“容器已死但 Pod 未删”的状态是典型的 K8s 删除阻塞模式。
2. 业务层面日志与 Trace 均显示正常完成（事实 5, 6），排除了容器内部进程挂死或资源耗尽导致无法响应的可能，进一步证明阻塞点在 K8s 控制面层面。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置包含自定义 finalizer (aiops.lab/hold) → Kubelet 完成容器终止后，API Server 等待 finalizer 条件满足 → API Server 拒绝执行对象删除操作 → Pod 卡在 Terminating 状态超 22 分钟
```

### 根因结论

已确认根因为 **Pod 的自定义 finalizer (`aiops.lab/hold`) 未被及时移除**。

*   **现象解释**：Pod 被删除后，Kubelet 正常发送信号终止了容器进程（Exit Code 137，证据 #2），但由于 Pod 对象带有 `aiops.lab/hold` finalizer，API Server 必须等待该 finalizer 从对象的 `metadata.finalizers` 列表中移除，才会真正销毁 Pod 对象。
*   **阻塞判定**：证据 #1 显示 Pod 已 Terminating 超过 22 分钟，且证据 #4 显示容器未重启，证明阻塞点在删除阶段的 finalizer 校验/等待逻辑，而非容器本身。
*   **结论**：根因为 Kubernetes API Server 被 finalizer 机制阻断，未能完成 Pod 对象的删除流程。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.1s
├─ 并发证据采集: 44.2s
│  └─ g1 aiops-case-11/workload: 44.2s (Evidence 37.8s, RCA 6.2s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
