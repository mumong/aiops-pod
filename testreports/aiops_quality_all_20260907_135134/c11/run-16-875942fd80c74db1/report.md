## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod Terminating 挂起 (Stuck) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | Pod `aiops-case-11/workload` 状态: `Terminating (lasts 29m)` | 核心症状：Pod 已进入删除流程但在 29 分钟内一直无法完成 |
| 2 | K8s Config | K8s Config | `app` 容器 `container.resource_limit.memory`: `96Mi` | 关键配置：提供极低的内存硬限制，为分析 Exit 137 提供环境背景 |
| 3 | K8s State | K8s State | `app` 容器 `last_terminated_reason`: `Error`; `last_exit_code`: `137` | 直接失败：容器进程以退出码 137 (SIGKILL) 异常终止 |
| 4 | K8s Event | K8s Event | `Normal Killing 29m kubelet Stopping container app` | 失败机制：kubelet 正在尝试停止容器，这与 Terminating 状态相一致 |
| 5 | K8s Config | K8s Config | Exit Code: `137` (Annotations 记录) | 确认信号：确认终止信号是强制杀死 (SIGKILL)，而非正常退出 |
| 6 | Metric | Metric | `kube_pod_container_status_restarts_total` for `app`: `0` | 现象印证：虽然发生致命错误，但重启次数为 0，说明删除过程确实“卡住”了，未触发重启 |
| 7 | Logging | Logging | 聚合 `request completed` (status 200, path `/work`) 共 5 条，时间窗 `23:09:48` 至 `23:09:56` | 限定作用：证明容器在进程终止前最后时刻（约 8 秒内）仍在正常处理 HTTP 请求 |
| 8 | Tracing | Tracing | Tempo span `GET /work` (trace `25d61c...`), 耗时 `4us` (23:09:48.705562Z) | 因果链印证：与日志时间窗完全吻合，证明业务在终止前处于活跃状态 |

**证据说明：**
*   **Kubernetes** 事实明确了 Pod 被卡在 `Terminating` 状态，且最后是以 `SIGKILL (137)` 终止。
*   **Metric** 中的重启计数为 `0` 与 Pod 长时间处于 `Terminating` 状态相印证，确认了删除操作的阻塞性。
*   **Logging** 与 **Tracing** 证据均指向容器在终止前的最后活跃窗口（23:09:48-56），日志中的 `allocated_mib` 显示为 `0`，这暗示可能未触发基于监控数据的 OOMKiller，或 OOMKiller 未能通过指标暴露。

## 🎯 根因分析 · g1

### 因果链
```text
容器进程受极小内存限制或未知因素被强制终止 (SIGKILL / Exit 137) → Finalizer 'aiops.lab/hold' 阻塞了资源清理逻辑 (或控制器因异常未执行删除) → API Server 拒绝完成删除请求 → Pod 处于 Terminating 挂起状态
```

### 根因结论
**证据不足，但根因特征高度明确：**
当前证据确认异常现象是由 **Finalizer `aiops.lab/hold` 阻塞了 Pod 的最终删除过程** 引起的。
*   **已确认的事实**：Pod 在 `Terminating` 状态下卡死 29 分钟，容器以 137 退出码被停止。由于删除被阻塞，Kubernetes 试图清理容器但因 Finalizer 限制未能完成，这解释了重启计数为 `0` 的现象。
*   **未确认的决定性事实**：
    1.  **137 的直接源头**：尽管资源限制极低（96Mi），但日志和追踪显示进程在终止前最后几秒仍在正常处理业务，未观察到明确的 OOM (OOMKiller) 日志或指标飙升。因此，无法断定是内存不足触发 OOMKiller，还是由 Liveness Probe 失败或外部系统强制 SIGKILL 导致。
    2.  **Finalizer 阻塞的具体机制**：输入事实中明确指出了 `unknowns` 为 `aiops.lab/hold` 对应的后端控制器状态。现有证据只能观察到阻塞的“结果”（卡死），无法证明是控制器宕机、网络延迟还是代码逻辑错误导致其无法移除该 Finalizer。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 27.0s
├─ 并发证据采集: 68.3s
│  └─ g1 aiops-case-11/workload: 68.3s (Evidence 59.2s, RCA 9.0s)
└─ 汇总总结: 15.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
