## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | {'message': 'k8s.v1.cni.cncf.io/network-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Normal Killing 39s kubelet Stopping container app` | 确认 kubelet 已在 39s 前发出停止信号 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy 30s kubelet Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 证实探针在容器内执行阻塞，暗示进程可能处于不可中断状态（如等待文件或 IO） |
| 3 | K8s Config | kubernetes | `container: app`，Memory Request `8Mi` / Limit `32Mi`；CPU Request `5m` / Limit `50m` | 排除因资源超限导致 OOMKilled 或系统限制导致异常终止的可能性 |
| 4 | K8s State | kubernetes | `Pod status: Terminating`, `phase: Running`, `restart_count: 0` | 确认 Pod 卡在终止循环中，且容器进程未退出（ExitCode 为 None） |
| 5 | Logging | elasticsearch | `application started` @ `07:30:21.003Z` | 记录应用启动时间点，作为终止逻辑的基准 |
| 6 | Logging | elasticsearch | `SIGTERM received; waiting` @ `07:30:22.492Z` | 直接证据：应用层捕获了信号但进入等待逻辑，是导致阻塞的直接原因 |

日志显示应用进程在收到 `SIGTERM` 后进入 `waiting` 状态，同时 Kubernetes Readiness 探针因等待执行 `os.path.exists` 操作而超时。这表明容器进程正在执行某种阻塞式检查，导致 Kubernetes 无法在宽限期（TerminationGracePeriodSeconds）内强制杀死容器，从而长期卡在 `Terminating` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用层优雅终止逻辑 (PreStop/Signal Handler) → 容器收到 SIGTERM 后轮询/等待外部信号 (/state/teardown-requested 文件) → 信号文件未就绪或依赖外部控制器创建 -> Pod 卡在 Terminating 阶段 (Container Running, Readiness Probes Timed Out)
```

### 根因结论

**证据不足**。

现有事实支持以下逻辑链条：
1. **确认现象**：Pod 处于 `Terminating` 状态，但容器仍在 `Running`（Evidence #4）；Kubelet 已发送 `SIGTERM`（Evidence #1），但容器未退出。
2. **确认机制**：应用日志显示进程在接收到 `SIGTERM` 后进入了 `waiting` 模式（Evidence #6）；探针超时（Evidence #2）印证了应用进程内部存在阻塞操作。
3. **缺失环节**：输入事实中**未包含**应用具体的代码逻辑、`terminationGracePeriodSeconds` 的具体数值（仅观察到长达未耗尽的终止时间），也**未包含**挂载卷 `/state/teardown-requested` 的实际存在状态。

虽然 RCA 描述指向 `/state/teardown-requested` 文件未就绪，但根据约束规则，未通过事实（如 PV 挂载检查或 exec 命令执行结果）验证该文件确实缺失或控制器未创建该文件。因此，当前证据仅能证明“应用存在阻塞终止逻辑”，无法确认该逻辑的具体缺陷或外部依赖故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.4s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-v13/workload: 43.1s (Evidence 31.9s, RCA 11.1s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
