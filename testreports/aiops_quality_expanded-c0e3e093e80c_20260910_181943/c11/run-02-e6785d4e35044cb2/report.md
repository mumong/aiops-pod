## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态卡住，无法删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason=Error`，`exit_code=137` | 确定容器因被强制终止而退出 |
| 2 | K8s Event | Kubernetes | `message="Normal Killing ... Stopping container app"` | 确认 kubelet 正常执行了停止容器的操作 |
| 3 | K8s Config | Kubernetes | `resource_limit.cpu=200m`，`resource_limit.memory=96Mi` | 提供资源配额上下文（资源未耗尽） |
| 4 | K8s State | Kubernetes | `pod.status=Terminating (lasts 2m47s)` | 确认 Pod 处于挂起的终止状态，且持续时间较长 |
| 5 | Metric | Prometheus | `container.restart_count=0` | 确认无异常重启行为，属于单次退出 |
| 6 | Logging | Elasticsearch | Pattern: `request completed, http_status=200, path=/work` (首次: `2026-09-11T03:47:09.905Z`) | 证明退出前应用层正常响应 HTTP 请求，应用无报错 |
| 7 | Tracing | Deepflow/Tempo | Trace `1edba7b...`: HTTP `GET /work` 200 OK (`start=03:47:09.905582Z`) | 验证最后一次业务请求在容器终止前已成功处理 |

**证据说明**：
- **业务正常性**：Logging 和 Tracing 证实 Pod 在 `03:47:09` 至 `03:47:15` 期间正常处理了多个 `/work` 请求并返回 200 状态码，排除了应用层逻辑错误导致崩溃的可能。
- **异常发生与终止**：`fact-6980c562c095` 和 `fact-92bccd7d25bb` 指出容器以 `exitCode 137` (SIGKILL) 退出，这是外部强制终止的典型标志。
- **状态卡住矛盾**：Kubelet 日志（`fact-ead13790309a`）表明它正常停止了容器，但 `fact-f8e42b530960` 显示 Pod 状态长达 2 分 47 秒仍卡在 `Terminating`。这表明 Kubernetes 对象本身在容器清理后，仍无法从 API Server 端完成删除流程。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了自定义 Finalizer 'aiops.lab/hold' → Finalizer 未满足/未被清理 → API Server 拒绝释放资源对象 → Pod 处于 Terminating 状态卡住
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-11/workload` 处于 `Terminating` 状态卡住，是因为该对象配置了自定义 Finalizer `aiops.lab/hold`。

证据链支撑：
1. **应用退出原因**：Logging 和 Tracing (`fact-f6128af0681d`, `fact-6f47a585addf`) 显示 Pod 退出前正常响应了请求，而 `exit_code=137` (`fact-92bccd7d25bb`) 和 `event="Killing"` (`fact-ead13790309a`) 证实容器是被外部系统（如用户执行 `kubectl delete`）强制终止的。
2. **删除阻塞机制**：在容器已成功停止且退出（`restart_count=0`）后，Pod 状态依然处于 `Terminating` (`fact-f8e42b530960`) 且持续数分钟。在 Kubernetes 机制中，这通常由 Finalizer 阻止。
3. **结论**：结合输入中的正式 RCA，正是 `aiops.lab/hold` 这个自定义 Finalizer 在容器终止后未被清理，导致 API Server 始终挂起该资源的释放操作。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.5s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-11/workload: 42.0s (Evidence 34.1s, RCA 7.8s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
