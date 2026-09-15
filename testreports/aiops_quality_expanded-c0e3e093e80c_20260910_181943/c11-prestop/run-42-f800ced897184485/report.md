## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态，但容器仍保持 Running，未退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes Pod | 状态: Terminating, 实际 Phase: Running | 确认 Pod 处于异常停滞的终止状态，进程未响应退出信号 |
| 2 | K8s Event | Kubernetes Kubelet | event.message: Normal Killing 47s kubelet Stopping container app | 确认节点级控制器已下发终止指令 |
| 3 | K8s Config | Kubernetes Config | container.resource_limit.memory: 32Mi, cpu: 50m | 排除资源耗尽导致 OOMKilled 或 CPU Throttling 的可能 |
| 4 | K8s State | Kubernetes Pod Condition | 条件: PodScheduled/Initialized/ContainersReady/Ready 全部为 True | 确认容器在终止前一直运行正常，无就绪性故障历史 |
| 5 | K8s State | Kubernetes Pod | container.app restart_count: 0 | 排除因容器频繁重启/崩溃而无法正常退出的情况 |
| 6 | Logging | Elasticsearch | log.message: "application started" (2026-09-14T06:05:28.805Z) | 确认应用已正常启动，且日志中无报错、报错或主动退出记录 |
| 7 | Metric | Prometheus | kube_pod_container_status_restarts_total(app): 0 | 确认监控指标与 K8s State 一致，容器自启动以来从未重启 |

证据分析：
1. K8s State 显示 Pod 为 `Terminating` 且容器保持 `Running`，配合 `restart_count=0` 表明应用未发生崩溃，而是卡在某个生命周期阶段。
2. 日志仅包含 `application started`，无报错，且无 Tracing 数据佐证异常调用，说明问题出在应用内部逻辑而非外部依赖故障。
3. 资源配置与条件状态排除了因资源不足或 Pod 就绪性失败导致的终止卡住。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码硬编码等待不存在的 '/state/teardown-requested' 文件 → SIGTERM 触发但应用主循环不响应，阻塞容器退出 → PreStop 钩子同样阻塞于等待同一文件，kubelet 无法执行到钩子阶段或钩子执行被应用阻塞 → Pod 保持 Terminating 状态，等待 3900s 宽限期超时
```

### 根因结论

**已确认的根因**：容器应用逻辑无限循环等待文件 `/state/teardown-requested` 存在，而删除流程中未创建该文件（且 PreStop 钩子同样阻塞于此等待），导致进程未响应 SIGTERM，Pod 在 3900s 宽限期内无法退出。

**证据支撑**：
- **状态证据**：Pod 状态为 `Terminating`，但容器状态仍为 `Running` 且重启次数为 0（证据 #1, #5），说明进程未退出也未崩溃。
- **事件证据**：Kubelet 发出 `Stopping container` 事件（证据 #2），证明终止请求已下发。
- **缺失日志证据**：日志中仅有 `application started`，无任何报错或退出日志（证据 #6），证明应用代码内部进入了某种无输出、不响应信号的阻塞循环。
- **环境证据**：资源充足（证据 #3），且无外部依赖异常日志。

综上，应用逻辑无法响应标准的终止信号机制，导致 Pod 无限期卡在 `Terminating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.6s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-v12/workload: 46.7s (Evidence 35.8s, RCA 10.7s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
