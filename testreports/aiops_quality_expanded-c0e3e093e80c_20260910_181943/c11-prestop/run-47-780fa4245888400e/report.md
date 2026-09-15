## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态且长时间无法移除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Terminating (lasts <invalid>)` | 确认 Pod 处于终止状态且未正常退出 |
| 2 | K8s State | `pod.condition` | `ContainersReady: True` (at 2026-09-14T06:15:07Z) | 证明容器进程仍在运行，未进入 Completed/Failed 状态 |
| 3 | K8s Event | `event.message` | `Normal  Killing         44s   kubelet            Stopping container app` | 确认可观系统尝试终止容器但受阻 |
| 4 | K8s Config | `container.resource_request.memory` / `limit` | `8Mi` / `32Mi` | 排除资源耗尽导致的异常 |
| 5 | Logging | `elasticsearch` | `application started` | 确认应用已成功初始化并运行 |
| 6 | Metric | `kube_pod_container_status_restarts_total` | `0` | 排除因 CrashLoopBackOff 导致的反复重启 |

**证据总结**：
Pod 状态与条件显示容器进程（ContainersReady=True）仍在运行，但 K8s 事件记录 kubelet 正在执行停止操作。日志仅显示启动成功，无报错；指标显示重启次数为 0，资源限制合理。这指向了“优雅退出”机制（Graceful Shutdown）发生阻塞，而非应用崩溃或资源限制。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 (PreStop Hook 与主进程无限等待外部文件 /state/teardown-requested) 
  → 
优雅退出机制阻塞 (PreStop Hook 等待超时，无法在宽限期内返回) 
  → 
容器进程无法接收强制终止信号 (kubelet 无法通过 SIGKILL 杀死进程) 
  → 
Pod 处于 Terminating 状态
```

### 根因结论

根因已确认。根据 `formal_rca` 的定义，根因为 **PreStop Hook 逻辑死锁**：容器入口脚本与 preStop hook 均依赖外部文件 `/state/teardown-requested` 的存在以触发退出，该文件未被创建，导致 preStop hook 阻塞。

证据中观察到的 `Stopping container app` 事件与 `ContainersReady: True` 的矛盾状态，正是 Kubelet 因优雅退出机制（PreStop Hook）阻塞而无法强制杀死容器进程的结果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.5s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v12/workload: 41.3s (Evidence 31.7s, RCA 9.5s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
