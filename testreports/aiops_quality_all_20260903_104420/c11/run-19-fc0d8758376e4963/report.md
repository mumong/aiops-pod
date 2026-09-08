## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态卡死 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Config | Pod `aiops-case-11/workload` 配置了自定义 finalizer `'aiops.lab/hold'` | 解释 Terminating 状态卡死的直接原因（需补充说明 finalizer 未清理） |
| 2 | K8s State | K8s State | Pod 当前状态为 `Terminating`，且 `ContainersReady` 为 `False` | 确认异常实体及卡死症状 |
| 3 | K8s State | K8s State | 容器 `app` 的 `last_exit_code` 为 `137` | 表明容器非正常退出（SIGKILL），排除了应用自身未处理关闭信号的常见可能 |
| 4 | K8s State | K8s State | 容器 `app` 的 `last_terminated_reason` 为 `Error` | 补充确认非正常终止原因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 当前值 `0`（样本数37，统计 min/max 均为 0） | 排除因重启风暴或 OOMKilled 频繁重启导致的异常 |

证据表明，Pod 容器已非正常终止（exit 137），但 API Server 未能清理该资源。根本阻碍在于 Kubernetes Garbage Collector 或 finalizer 控制器在等待自定义 finalizer `'aiops.lab/hold'` 对应的清理操作完成，而清理控制器或逻辑未执行或卡住，导致资源无法从 API Server 移除。

## 🎯 根因分析 · g1

### 因果链

```text
未执行的清理逻辑（针对 finalizer 'aiops.lab/hold'） → Kubernetes Garbage Collector 等待清理完成 → Pod 资源无法从 API Server 移除 → Pod 长期处于 Terminating 状态
```

### 根因结论

已确认根因：Pod YAML 中配置了自定义 finalizer `'aiops.lab/hold'`，该 finalizer 对应的清理控制器或逻辑未执行或卡住，导致 Kubernetes API Server 无法移除 Pod 资源对象。

此结论由以下事实支撑：
- `K8s State` 中的 `finalizer 'aiops.lab/hold'`（证据 #1）与 `Terminating` 状态（证据 #2）结合，表明标准终止流程被该 finalizer 阻塞。
- `K8s State` 中的 `exit_code 137`（证据 #3）和 `terminated reason Error`（证据 #4）确认了 Pod 终止是由外部信号或错误触发，而非应用自身优雅关闭逻辑问题。
- `Metric` 显示重启次数为 0（证据 #5），进一步排除了因反复重启导致的终止卡顿，确认卡死发生在首次终止阶段。

缺失的决定性事实：自定义 finalizer `'aiops.lab/hold'` 的具体实现代码及为何未自动清理的具体原因（需检查对应 Operator/Webhook 日志）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.5s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-11/workload: 55.2s (Evidence 46.1s, RCA 9.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
