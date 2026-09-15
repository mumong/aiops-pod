## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'message': 'Annotations:               cni.projectcalico.org/containerID: 744106ac27c283ef01b16aad0750a9ad5cca5ad6c3bd279888d310c83aa8c7b0'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | Running | 容器进程仍在运行，未正常退出 |
| 2 | K8s State | pod.status | Terminating (lasts <invalid>) | Pod 处于强制终止阶段，未进入 Completed/Failed |
| 3 | K8s Config | container.resource_limit.memory | 32Mi | 排除因内存资源不足（OOM）导致进程异常退出 |
| 4 | K8s Config | container.resource_request.cpu | 5m | 排除因 CPU 资源严重争抢导致进程假死 |
| 5 | K8s Event | event.message | Normal Killing / Stopping container app | 确认 kubelet 已发起停止流程 |
| 6 | Logging | log.message | application started (2026-09-14T04:48:36.705Z) | 证明应用已正常启动，后续无应用层日志输出 |

**证据说明：**
1. 证据 1、2、5 互相印证：Pod 处于 Terminating 状态且 kubelet 报告正在停止容器，证明正常的终止信号已送达。
2. 证据 1、3、4 互相印证：在资源限制充足且容器状态显示仍在运行的情况下，排除了资源耗尽导致的异常崩溃。
3. 证据 6 与证据 5 形成逻辑断层：应用启动后无后续报错日志，但进程未随终止信号退出，结合缺失的 exec 探针日志，指向应用侧可能在等待特定条件（如文件写入），而非处理崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Pod被删除（deletionTimestamp设置） → kubelet发送SIGTERM并执行preStop hook → 容器主进程与preStop hook均阻塞等待 /state/teardown-requested 文件 → Pod处于Terminating状态，容器未退出
```

### 根因结论

**证据不足。**
现有事实仅能证实 Pod 处于异常阻塞的 Terminating 状态（证据 1, 2, 5），且应用启动正常且非资源限制问题（证据 3, 4, 6）。虽然 RCA 模型推测原因为“等待 `/state/teardown-requested` 文件”，但输入事实中**明确标注无法确认该文件是否存在**，也**缺乏 preStop hook 运行状态或写入逻辑的关键证据**（如宿主机文件查询或 sidecar 日志）。因此，无法区分这是预期的长等待机制生效还是异常阻塞，不能发布确切的根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-v12/workload: 46.2s (Evidence 36.4s, RCA 9.7s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
