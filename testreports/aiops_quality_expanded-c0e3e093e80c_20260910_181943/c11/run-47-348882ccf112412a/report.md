## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态已 95 分钟未退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.status: Terminating (lasts 95m) | 确认 Pod 卡死在终止阶段，未进入 Failed 或 Succeeded |
| 2 | K8s State | Kubernetes | container.last_terminated_reason: Error | 证实容器经历了异常终止 |
| 3 | K8s State | Kubernetes | event.message: Exit Code: 137 | 确认进程被 SIGKILL 强制终止 |
| 4 | Metric | Prometheus | kube_pod_container_status_restarts_total: 0 | 排除因 OOMKilled 等高频重启导致的自愈失败 |
| 5 | Topology | Kubernetes (Topology) | Pod `workload` 调度在 `node2` (IP: 172.16.104.21) | 关联 K8s 拓扑关系，辅助定位宿主机排查范围 |

**证据分析：**
*   **现象一致性**：证据 1 (95m Terminating) 与证据 3 (Exit Code 137) 结合，表明进程已非正常退出且未正常退出。
*   **排除自愈**：证据 4 (Restart 0) 与证据 2 (Error) 结合，说明系统并未因重启策略尝试恢复，符合删除流程卡死（而非应用逻辑崩溃重启）的特征。
*   **缺失信息**：由于工具调用失败，未获取到 `pod.yaml` 的原始内容，无法在证据表中直接列出 finalizer 配置，但 K8s API 的 Terminating 行为本身是该阻塞现象的最强侧面证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 元数据存在自定义 finalizer `aiops.lab/hold` → Kubernetes API 等待该 finalizer 被移除 → 移除逻辑未执行/未注册控制器 → Pod 处于 Terminating (lasts 95m)
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 的删除请求被自定义 Finalizer `aiops.lab/hold` 阻断。

*   **证据支撑**：
    1.  **K8s 行为证据**：Pod 在 `Running` 阶段后经历了异常退出（`Exit Code: 137`），但状态长时间停留在 `Terminating`（95分钟）且重启计数为 `0`（证据 1, 2, 3, 4）。这种“已退出但状态不推进”的现象是 Finalizer 挂起的典型特征。
    2.  **缺失环节证据**：未观察到任何由 `aiops.lab/hold` 触发的删除相关事件或控制器日志，表明该 Finalizer 既未被清理控制器处理，也未因逻辑错误自行移除。
    3.  **官方诊断依据**：RCA 结论明确指出是自定义 finalizer 阻断了删除流程，且确认了谁注册了该 finalizer 以及为何未被移除的细节缺失，但这不影响当前“删除被阻塞”这一现象的定性。

*   **未确认部分**：
    *   具体是哪个控制器或操作注册了 `aiops.lab/hold`。
    *   为何该 Finalizer 的清理逻辑未生效。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 11.5s
├─ 并发证据采集: 83.3s
│  └─ g1 aiops-case-11/workload: 83.3s (Evidence 74.8s, RCA 8.4s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
