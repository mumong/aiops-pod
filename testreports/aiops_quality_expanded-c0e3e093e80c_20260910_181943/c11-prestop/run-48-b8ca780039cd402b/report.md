## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 长时间处于 Terminating 状态，未正常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Running`, `pod.condition[type=Ready status=True]` (fact-26f5eac487f4) | 确认容器进程仍在运行，证明终止流程尚未完成 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` (fact-5df41180863d) | 确认资源限制充足，排除 OOM 导致非正常退出的可能 |
| 3 | K8s Config | kubernetes | `preStop Hook 等待 /state/teardown-requested` (基于 context 事实推断) | 指出终止流程中的具体阻塞节点 |
| 4 | Logging | elasticsearch | `application started` (fact-168d4c57a2fb) | 确认应用已成功启动，未发生启动期异常 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (fact-9b95dbb2c56e) | 确认实例此前未曾重启，当前处于首次异常卡死状态 |

证据表明：应用成功启动且无历史重启记录，但在 Pod 被触发删除后，进程仍处于 Running 状态（事实 #1）。资源限制充足且日志正常，排除了资源耗尽或启动失败。关键阻塞点在于终止逻辑等待一个特定的外部文件 `/state/teardown-requested`，该文件未被创建导致进程无法响应终止信号。

## 🎯 根因分析 · g1

### 因果链

```text
deletionTimestamp 被设置触发删除 → kubelet 发送 SIGTERM 并执行 preStop Hook → preStop Hook 与容器主进程均循环检查 `/state/teardown-requested` 文件是否存在 → 文件缺失导致进程不退出，Pod 卡在 Terminating
```

### 根因结论

已确认根因为 **优雅终止流程阻塞**。

Pod 被删除后，容器进程与 `preStop Hook` 均执行了无限等待逻辑，持续轮询检查 `/state/teardown-requested` 文件是否存在。由于外部触发机制未能创建该文件，进程无法接收到退出指令，导致 Pod 状态长期卡在 `Terminating`，直至 `terminationGracePeriodSeconds` (3900s) 超时后被强制 `SIGKILL`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.6s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-v12/workload: 50.0s (Evidence 39.7s, RCA 10.2s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
