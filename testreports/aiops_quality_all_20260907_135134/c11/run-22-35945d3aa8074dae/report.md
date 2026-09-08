## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | {'message': 'k8s.v1.cni.cncf.io/network-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s API | `Pod status: Terminating (lasts 37m)` | 证明 Pod 已进入终止状态并持续挂起，属于直接故障现象 |
| 2 | K8s Config | K8s Config | `memory limit: 96Mi` / `cpu limit: 200m` | 提供容器资源边界信息，用于排查 OOMKilled |
| 3 | K8s State | K8s API | `container last_terminated_reason: Error` / `exit_code: 137` | 记录容器非正常退出，需结合后续事件确认是内核 Kill 还是应用退出 |
| 4 | K8s Event | K8s API | `Normal Killing, 37m ago, message: "Stopping container app"` | 明确容器进程是被外部停止（Killing），支持 Exit 137 (SIGKILL) 的归因 |
| 5 | K8s Config | K8s Config | `Annotations: cni.projectcalico.org/containerID: be718c7097...` | 确认 CNI 插件及网络状态正常，排除 CNI 插件故障导致的 Pod 异常 |

证据链表明：容器在运行 37 分钟后收到外部停止信号（`Killing` 事件），导致进程被 Kill（`Exit 137`）并进入 Terminating 状态。虽然资源限制较小（96Mi/200m），但当前 K8s 事件未体现 OOMKill 迹象。Pod 状态一直停留在 `Terminating` 达 37 分钟未彻底消失，核心问题指向 Pod 删除阶段的阻塞点。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程被外部终止 (Exit 137) → Pod 触发删除流程 (Terminating) → [未确认] Finalizer 阻塞导致删除挂起 (37m) → [未确认] 容器终止的确切触发源 (资源超限/手动干预/应用错误)
```

### 根因结论

**证据不足。**

正式 RCA 指向“未知的 Pod Finalizer 导致删除挂起”，但根据诊断约束条件，该结论无法发布：

1.  **阻断原因**：诊断配置明确标记 `RCA fact binding and publication validation disabled by configuration`。正式结论中的 `diagnosis_publishable` 状态为 `false`。
2.  **证据缺失**：
    *   `Pod metadata.finalizers` 列表内容未知，无法通过事实确认具体是哪个 Finalizer 导致了阻塞。
    *   `Pod status.conditions` 中 DeletionTimestamp 与实际删除尝试的具体时间线缺失。
    *   导致容器 Exit 137 (SIGKILL) 的底层触发原因（如 OOM Kill、应用崩溃、或外部手动 Kill 脚本）缺乏决定性事实支持。

因此，本次诊断确认为：Pod 异常终止且删除挂起，但确切阻碍删除的 Finalizer 列表以及容器进程被 Kill 的根本原因，现有证据不足以确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 8.4s
├─ 并发证据采集: 52.4s
│  └─ g1 aiops-case-11/workload: 52.4s (Evidence 44.1s, RCA 8.2s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- 未调用 Runbook
