## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | `Running` | 描述 Pod 当前生命周期阶段 |
| 2 | K8s State | pod.condition | `Ready=False` (ContainersNotReady: app), `ContainersReady=False` | 确认应用容器 `app` 处于不健康状态 |
| 3 | K8s State | container.last_terminated_reason | `Error` | 指向容器非正常退出的直接原因 |
| 4 | K8s State | container.last_exit_code | `137` | 指示容器被操作系统或 kubelet 强制终止（OOMKilled 或 SIGKILL） |
| 5 | K8s Config | container.resource_request.cpu | `20m` | 调度预留资源参考 |
| 6 | K8s Config | container.resource_limit.cpu | `200m`, memory=96Mi | 定义容器资源硬限制 |
| 7 | Metric | kube_pod_container_status_restarts_total | `0` | 提供历史重启次数的绝对基准值 |
| 8 | Metric | kube_pod_status_phase | Running=1, Pending=0 | 从监控视角验证当前运行状态 |

证据 1-4 共同刻画了一个在 `Running` 阶段发生异常退出的容器现象，退出码 `137` 与终止原因为 `Error` 高度吻合。然而，证据 8（Metric）提供的 `restart_count=0` 与 K8s State 中记录的 `last_terminated_reason=Error` 存在逻辑冲突——通常异常退出会导致重启计数增加，除非重启策略未配置或重启尚未触发，当前数据不足以判断该退出是单次偶发还是持续阻断状态。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：Pod 存在自定义 finalizer 'aiops.lab/hold'，且持有者未移除该 finalizer
→ 失败机制：API Server 无法执行资源清理，Pod 进入 Terminating 状态并卡住
→ 直接失败：Pod 无法完成销毁，容器状态异常（Running 且 Terminating 并存）
→ 用户可见现象：集群中存在状态为 Terminating 但无法删除的 Pod 对象
```

### 根因结论

现有证据支持 Pod 当前被 `aiops.lab/hold` finalizer 阻止删除，这是导致其卡在 Terminating 状态的直接原因。但是，正式根因判定为**证据不足**。

原因在于：
1. **缺失持有者定位**：工具未返回关于哪个 Controller 或外部系统注册并持有该 finalizer 的信息。
2. **RCA 校验被禁**：配置显示 `RCA fact binding and publication validation disabled`，导致无法确认上述链条是否经过最终校验发布。
3. **现象矛盾未解**：虽然 exit_code=137 暗示资源问题（如 OOM），但在 finalizer 阻断的上下文中，必须优先解释为何 Pod 处于 Terminating 而非 Pending/CrashLoop，且需解释 restart_count=0 的状态，目前这些细节缺乏决定性事实支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.2s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-11/workload: 39.4s (Evidence 31.8s, RCA 7.5s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
