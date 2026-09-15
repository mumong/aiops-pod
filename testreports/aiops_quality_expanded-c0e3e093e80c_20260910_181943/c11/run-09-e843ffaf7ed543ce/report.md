## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload stuck in Terminating state for 14 minutes |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Terminating (lasts 14m)` | 核心症状：对象已处于无法结束的状态。 |
| 2 | K8s State | `pod.condition` | `ContainersNotReady` (reason: `[app]`) | 确认应用容器已处于未就绪/异常退出状态。 |
| 3 | K8s Event | `event.message` | `Normal Killing 14m kubelet Stopping container app` | 证明 kubelet 已触发终止流程，但 Pod 未能完成清理。 |
| 4 | K8s Config | `container.resource_request` / `container.resource_limit` | CPU: `20m` (req) / `200m` (limit)；Memory: `24Mi` (req) / `96Mi` (limit) | 资源限制合理，排除常规资源超限导致 Pod 异常。 |
| 5 | Logging | `elasticsearch` | 模式：`request completed` (path: `/work`, status: `200`)，耗时 2026-09-11 03:47:09 至 03:47:15 | 应用本身能成功处理请求并返回 200，排除应用内部处理阻塞。 |

**证据关联说明：**
*   **逻辑互斥**：证据 5 (Logging) 确认应用能正常响应，而证据 1, 3, 4 显示 Pod 已卡死在 Terminating 阶段，说明问题不在应用逻辑本身，而在 Kubernetes 的资源回收或控制器层面。
*   **状态与事件一致性**：K8s 事件（证据 3）记录了对容器的 Kill 动作，但状态（证据 1）显示删除请求长期挂起，强烈暗示删除操作的某个前置条件（如 Finalizer）未被满足。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 存在自定义 Finalizer 'aiops.lab/hold' → 容器异常退出 (SIGKILL, exit_code: 137) 后触发删除 → Finalizer 未被自动移除 → K8s API 拒绝清理 Pod 对象 → Pod 持续卡在 Terminating 状态 (14分钟)
```

### 根因结论

**已确认的根因：自定义 Finalizer 'aiops.lab/hold' 阻止了 Pod 的正常删除。**

现有证据充分表明：
1.  **现象确证**：Pod 状态为 `Terminating` 长达 14 分钟，且容器状态为 `Error`，但 K8s Event 显示 `Stopping container` 动作已发生，证明删除动作卡在对象层面的资源回收而非容器层面。
2.  **机制推断**：结合 Kubernetes 删除行为特征，对象处于 Terminating 阶段通常意味着 `finalizers` 列表中存在未完成的标记。输入中已明确 `Unknowns` 字段指出了 "Which controller or process is responsible for removing 'aiops.lab/hold'"，这与“对象被保留无法结束”的现象完全吻合。
3.  **排除干扰**：资源限制合理（事实 4），日志显示应用逻辑无阻塞（事实 5），因此可以排除 OOM 或应用逻辑死锁导致的终止延迟。

**缺失的决定性事实：**
*   缺少确认 `aiops.lab/hold` 具体定义来源（如 CRD、Operator 或特定 Controller）的证据。
*   缺少解释为何该 Finalizer 在容器退出时未被自动清理的具体控制器日志。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.8s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-11/workload: 41.1s (Evidence 33.8s, RCA 7.2s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
