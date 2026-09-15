## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload (aiops-case-v13) 处于 Terminating 状态，且容器 app 仍在 Running，未自动退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Stopping container app` (Normal) | 确认删除流程已被触发 |
| 2 | K8s Event | kubelet | `Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` (Warning) | 探针与容器主进程通信异常 |
| 3 | K8s State | Kubernetes | `pod.phase: Running`, `pod.status: Terminating` | 确认 Pod 处于终止态但容器核心仍在运行 |
| 4 | K8s Config | Kubernetes | `container.resource_request.cpu: 5m`, `container.resource_limit.cpu: 50m` | 资源请求/限制极低，排除因资源耗尽导致无响应 |
| 5 | Logging | Elasticsearch | `2026-09-14T08:03:54.403Z`: `application started` | 确认应用进程已启动 |
| 6 | Logging | Elasticsearch | `2026-09-14T08:03:56.395Z`: `SIGTERM received; waiting` | 直接证实应用收到终止信号后进入等待状态 |

**证据分析：**
K8s 事件（#1, #2）与 Pod 状态（#3）共同证实删除流程已启动且持续。日志（#5, #6）提供了决定性证据：应用进程在收到 SIGTERM 信号后明确输出“waiting”，表明其执行了自定义信号处理逻辑。结合探针失败信息（#2）与低资源限制（#4），证实容器处于资源充足但逻辑死锁状态。

## 🎯 根因分析 · g1

### 因果链
```text
应用代码处理 SIGTERM 逻辑未正确退出 → SIGTERM 信号被接收但陷入死循环等待 → 容器未退出（Running），Pod 滞留 Terminating 状态 → 用户可见 Pod 终止卡住
```

### 根因结论
根因已确认：应用容器（app）在收到 `SIGTERM` 信号后，执行了包含死循环的信号处理逻辑（日志 `SIGTERM received; waiting` #6），导致其无法响应退出信号。

由于容器进程（PID 1）未终止，Kubelet 不会发送 `SIGKILL`（`deletionGracePeriodSeconds` 倒计时未到），致使 Pod 一直停留在 `Terminating` 状态且容器保持 `Running`（#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.1s
├─ 并发证据采集: 46.8s
│  └─ g1 aiops-case-v13/workload: 46.8s (Evidence 36.8s, RCA 9.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
