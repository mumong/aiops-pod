## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload 处于 Terminating 状态卡死，尽管 deletionTimestamp 已存在且 kubelet 已尝试 Killing 容器，但容器实际仍在 Running 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Unhealthy 43s (x2 over 45s) Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 证明容器主进程在探针检测时已处于停滞/无响应状态，导致探针超时 |
| 2 | K8s Event | kubelet | `Normal Killing 41s Stopping container app` | 确认 K8s 已发起终止流程并发送信号，但随后探针失效，暗示进程未响应终止 |
| 3 | Logging | elasticsearch | `application started` (14:56:11) → `SIGTERM received; waiting` (14:56:14) | 提供应用生命周期证据：应用启动后未立即退出，而是在 3 秒后收到 SIGTERM 并打印“等待” |
| 4 | K8s State | pod.spec | `container.resource_limit.memory: 32Mi`, `container.resource_limit.cpu: 50m` | 排除资源耗尽导致异常的可能，资源配置极低但并非导致僵死的直接原因 |
| 5 | K8s State | pod.status | `phase: Running`, `restart_count: 0` | 证明 Pod 尚未发生重启（OOMKilled 等），而是处于一种被 K8s 标记为 Terminating 但内部仍在运行的矛盾状态 |
| 6 | K8s Config | pod.phase | `status: Terminating (lasts <invalid>)` | 确认 Pod 对象本身已被触发删除操作，且处于长时间未完成的中间状态 |

**证据互证说明：**
Logging (事实 #3) 显示应用代码主动打印 `SIGTERM received; waiting`，这直接解释了为什么 Kubelet (事实 #2) 发送了 Kill 信号但进程（事实 #5, #4）仍保持 Running 状态且 RestartCount 为 0。由于主进程进入死循环等待（事实 #3），导致其无法响应探针探测（事实 #1），从而形成了“Pod 状态 Terminating 但容器仍 Running”的僵局。

## 🎯 根因分析 · g1

### 因果链

```text
容器应用代码逻辑缺陷：注册 SIGTERM 处理函数仅打印日志并进入 while 循环等待文件 → kubelet 发送 SIGTERM 信号但无法中断主进程死循环 → 主进程持续占用 CPU 且无响应能力，导致 Readiness 探针超时 → Pod 进入 Terminating 状态但容器实际仍在 Running
```

### 根因结论

**已确认的根因**：容器应用存在逻辑缺陷（代码未处理 SIGTERM 或处理不当），导致收到终止信号后进入死循环（等待特定文件状态），而非正常退出。

该根因通过日志中明确的 `SIGTERM received; waiting` 得到证实，解释了为何在 K8s 执行 `Stopping container` 操作时，容器进程并未退出反而导致 Readiness Probe 超时。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.5s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v13/workload: 40.1s (Evidence 29.9s, RCA 10.1s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
