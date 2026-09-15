## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 卡在 Terminating 状态，kubelet 已发出 Stopping 信号但容器未退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating | 确认 Pod 处于强制终止滞留状态 |
| 2 | K8s Event | Kubernetes | `Normal Killing ... Stopping container app` (fact-f1447ddafadc) | 确认 kubelet 已在 66s 前发送停止信号 |
| 3 | K8s State | Kubernetes | `pod.restart_count`: 0 (fact-0d574a6aef94) | 确认容器未发生异常重启，终止是唯一的近期变更 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-5ba1528f3d95) | 独立验证容器自启动以来未发生过重启 |
| 5 | Logging | Elasticsearch | `application started` (fact-8b2d2113877b, ts: 05:29:15Z) | 确认容器自 05:29:15Z 起保持运行且未输出终止日志 |
| 6 | K8s Config | Kubernetes | `resource_limit.memory`: 32Mi (fact-1195b13b1d87) | 排除内存超限导致的 OOM Kill |

**证据印证**：K8s 事件与状态（#1, #2）共同证实系统已发起强制终止，而应用日志（#5）持续显示“已启动”且 Restart Count 为 0（#3, #4），表明容器进程未响应终止信号，陷入无限阻塞。配置事实（#6）排除了资源限制相关的强制中断。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑缺陷：主进程与 PreStop Hook 无限阻塞等待文件 `/state/teardown-requested` → 终止条件未满足，进程无法退出 → kubelet 等待超时（terminationGracePeriodSeconds: 3900s）→ Pod 滞留 Terminating 状态
```

### 根因结论

已确认根因：应用代码逻辑缺陷。
*   **机制分析**：正式 RCA 指出，容器的主进程和 PreStop hook 均设置了无限循环，等待特定文件 `/state/teardown-requested` 存在。
*   **现象解释**：由于该文件未被创建，阻塞循环无法退出，导致容器进程在收到 SIGTERM 后无法执行退出逻辑，从而引发 Pod 滞留 Terminating。证据中的应用日志“application started”（#5）与长期运行的状态（#1）相一致，未显示任何异常退出或资源耗尽的提示。
*   **局限性**：关于文件 `/state/teardown-requested` 未被创建的具体触发失败原因（上游调度或应用逻辑），目前证据不足，标记为未知。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 28.0s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-v12/workload: 48.5s (Evidence 38.5s, RCA 10.0s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
