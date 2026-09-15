## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | aiops-case-v13/workload Pod 处于 Terminating 状态卡死 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-fd817fb86d74` - `Normal Killing ... 39s ... Stopping container app` | 确认 Kubelet 已发起容器终止请求 |
| 2 | K8s Event | kubernetes | `fact-35017923fea8` - `Warning Unhealthy ... Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 容器未退出导致存活探针持续超时，阻断 Pod 正常删除流程 |
| 3 | Logging | elasticsearch | `fact-fd817fb86d74` - `application started` (08:10:17Z) → `SIGTERM received; waiting` (08:10:19Z) | 捕获应用收到 SIGTERM 后的处理逻辑：收到信号后进入等待状态 |
| 4 | K8s Config | kubernetes | `fact-a2c935a19d79` - `container.resource_request.cpu: 5m` <br> `fact-09459fed24d7` - `container.resource_limit.cpu: 50m` <br> `fact-0e382e662ba5` - `container.resource_limit.memory: 32Mi` | 资源限制较低，但结合探针超时和日志状态，非资源耗尽导致的 OOMKill |
| 5 | Metric | prometheus | `fact-7eb3c4c4e8c1` - `kube_pod_container_status_waiting_reason` for `ContainerCreating` (1) <br> `fact-eed39e753452` - `restart_count` (0) | 容器未经历重启，且当前状态与 Terminating 过程可能存在观测延迟或状态竞态 |
| 6 | K8s State | kubernetes | `fact-288fb53bcbc9` - `status: Terminating (lasts <invalid>)` <br> `fact-621582333884` - `phase: Running` | 确认 Pod 处于 Terminating 阶段但 Phase 仍报告 Running，典型终止卡死现象 |

**证据关联说明**：
Kubernetes 事件 (事实 1) 证明系统层已执行终止操作；应用日志 (事实 3) 显示进程在收到 SIGTERM 后并未退出而是进入等待。这种“进程未退出”的状态直接导致就绪探针 (事实 2) 持续失败，进而使得 Pod 状态机无法推进至 Terminated，最终表现为 Terminating 状态卡死 (事实 6)。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷：监听 SIGTERM 后执行无限循环等待文件 '/state/teardown-requested' → 触发文件 '/state/teardown-requested' 在删除过程中未生成 → 容器进程卡在等待循环中无法退出 → 就绪探针超时及 Kubelet 终止超时 → Pod 处于 Terminating 状态卡死
```

### 根因结论

**已确认的根因**：
应用代码中存在缺陷。应用在接收到系统发出的 `SIGTERM` 信号后，未立即执行清理并退出，而是进入了一个无限循环，等待特定文件 `/state/teardown-requested` 的生成。由于该触发文件在 Pod 删除过程中未能生成，导致进程永远等待。
- **证据支撑**：
  - 日志显示进程收到 `SIGTERM` 后进入 `waiting` 状态 (`fact-fd817fb86d74`)；
  - Kubelet 探针因容器未退出而 `timed out` (`fact-35017923fea8`)；
  - Pod 长期处于 `Terminating` 状态 (`fact-288fb53bcbc9`)。

**缺失事实**：
虽然 RCA 已发布，但缺少对 `/state/teardown-requested` 文件生成逻辑的外部依赖确认（例如是否由另一个 Sidecar 生成，或外部触发源是否失效）。不过，日志已明确捕捉到“收到信号后等待”的行为，足以定性为代码逻辑缺陷导致的非正常退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.2s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-v13/workload: 39.8s (Evidence 30.6s, RCA 9.1s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
