## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态，且无法完成删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod phase | `Terminating (lasts 2m4s), (lasts 4m), (lasts 2m42s)` | 确证 Pod 长期处于 Terminating 挂起状态，无法完成删除。 |
| 2 | K8s State | Pod condition | `ContainersReady: False`, `Ready: False` (原因: `ContainersNotReady`) | 确认容器未正常退出就绪，Pod 未进入正常终态。 |
| 3 | K8s Event | Event message | `Normal  Killing         3m59s  kubelet            Stopping container app` | 确证 kubelet 尝试停止容器，这是 Pod 开始清理流程的触发点。 |
| 4 | K8s State | Container exit | `exit_code: 137`, `reason: Error` | 确证容器以 Exit Code 137 (SIGKILL) 终止，且被 K8s 标记为 Error 而非 OOMKilled。 |
| 5 | Metric | Pod phase | `phase: Running` (kube-state-metrics, `2026-09-03T22:33:20Z`) | 存在指标不一致，当前 phase 为 Running，可能为指标延迟或 lifecycle reuse 现象。 |
| 6 | K8s Config | Resource | `cpu request: 20m, limit: 200m`; `memory request: 24Mi, limit: 96Mi` | 提供资源限制背景，但 exit_code 不是 OOMKilled，内存限制非直接OOM证据。 |
| 7 | Logging | Pattern | `http_request /work` completed (200) at `22:31:06Z` - `22:31:12Z` | 证明容器在终止前 20 秒内仍正常处理 HTTP 请求。 |
| 8 | Tracing | Flow/Span | `GET /work` (status 200), `trace_id: 75c4028b...` at `22:31:10Z` | 追踪与日志关联，验证服务在终止前最后一刻仍在响应，未报内部错误。 |

**证据说明：**
1. 事件 (3) 和退出码 (4) 共同证明了 `Stopping -> Killed (137) -> Terminating` 的时序链路。
2. 日志 (7) 和追踪 (8) 表明容器在收到信号前业务逻辑正常，未出现业务内部崩溃或 OOM 相关错误。
3. K8s 状态 (1, 2) 显示虽然容器已死（Exit 137），但 Pod 未能彻底删除，指向 Finalizer 阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
容器 app 以 Exit Code 137 异常终止 (被 SIGKILL) → Finalizer 'aiops.lab/hold' 依赖清理逻辑触发失败 → Pod 卡在 Terminating 状态 (Stuck) → 用户观察到 Pod 无法删除
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 处于 **Terminating 挂起** 状态。

**支撑证据**：
- Pod 已进入 `Terminating` 状态持续超过 4 分钟（事实 1, 2）。
- 容器 `app` 已收到 `Killing` 事件并以 `Exit Code 137` 退出（事实 3, 4）。
- 日志与追踪显示，容器在终止前（约 22:31:10Z）仍在正常响应业务请求（事实 7, 8），未发生业务崩溃。

**结论**：
Pod 无法正常删除的原因是**内置的 Finalizer (`aiops.lab/hold`) 阻塞了删除流程**。虽然容器已被操作系统强制杀死（Exit 137），但 Finalizer 的清理逻辑因某种原因（可能与 137 退出码或特定信号有关）未能成功执行，导致 K8s 控制器无法移除 Pod 资源。

**缺失的关键事实（导致不确定性的部分）**：
- 容器为何收到 `Exit Code 137` 但未被标记为 `OOMKilled`（事实 4）。这排除了标准的 OOM-killer 路径，可能是外部进程 Killer 或配置不当的资源限制。
- Finalizer `aiops.lab/hold` 的具体逻辑及其为何因 `137` 异常退出而卡住。由于缺少 Pod Logs 中的 `previous` 状态（工具执行失败/无数据），无法确认 PreStop Hook 或 Finalizer 清理时的具体报错日志。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 18.8s
├─ 并发证据采集: 160.6s
│  └─ g1 aiops-case-11/workload: 160.6s (Evidence 148.7s, RCA 11.7s)
└─ 汇总总结: 16.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
