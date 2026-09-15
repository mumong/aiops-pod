## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'Initialized', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Running` / `pod.status: Terminating` | 核心矛盾：Pod 逻辑状态为终止中，但容器实际仍在运行。 |
| 2 | K8s Event | kubernetes | `Normal Killing Stopping container app` (fact-2d0ddae5d345) | 确认 kubelet 已尝试正常删除，但并未成功终止容器。 |
| 3 | Metric | prometheus | `container: app` 的 `kube_pod_container_status_restarts_total` = 0 | 容器自启动后未发生过重启，说明进程并未崩溃，而是持续运行。 |
| 4 | K8s Config | kubernetes | `limit.cpu: 50m`, `limit.memory: 32Mi` | 资源限制设置偏低，但在无重启迹象下暂无法直接解释停滞。 |
| 5 | Logging | elasticsearch | `application started` (fact-1e780524ebbe) | 确认应用进程已启动，但缺失应用级关于“停止”或“清理”的动作日志。 |

**证据说明**
1. **Kubernetes 状态与事件的直接冲突**：事件确认了 SIGTERM 信号已发出，但 `phase: Running` 且重启次数为 0，表明进程忽略了信号或在后台线程中阻塞，并未退出。
2. **缺失关键诊断事实**：`kubectl_get_yaml` 工具因 YAML 解析失败（`yaml_parse_failed`）而返回了代码片段而非配置，导致无法确认是否存在 `preStop` 钩子或导致阻塞的代码逻辑，使得上述冲突的原因被锁定在未知的“应用内部逻辑”中。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 删除请求 (deletionTimestamp 存在) → kubelet 发送 SIGTERM (Normal Killing) → 容器进程未退出 (restart_count: 0, phase: Running) → Pod 持续卡在 Terminating 状态
```

### 根因结论

**证据不足。**

当前事实显示 Pod 卡在 `Terminating` 状态是因为容器进程（`app`）在收到 `Stopping container` 信号后依然保持 `Running` 状态。然而，导致该现象的决定性原因无法确诊：
1. **配置校验缺失**：关键工具 `kubectl_get_yaml` 执行失败（返回 `yaml_parse_failed`），导致无法验证 Pod Spec 中是否存在阻塞性的 `preStop` 生命周期钩子，也无法确认应用代码逻辑（如 `teardown-requested` 检查）是否存在。
2. **应用日志缺失**：缺乏应用内部关于关闭流程的具体日志，无法判断是应用主动忽略了终止信号，还是在执行清理任务时发生了死锁。

在 YAML 配置无法读取且无更多应用层日志的情况下，无法排除是配置问题还是代码逻辑问题，故根因判定为“证据不足”。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.6s
├─ 并发证据采集: 95.2s
│  └─ g1 aiops-case-v12/workload: 95.2s (Evidence 84.1s, RCA 11.0s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
