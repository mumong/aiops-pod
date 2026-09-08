## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 处于 Terminating 状态超过54分钟，未能从 API Server 删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: "Terminating (lasts 54m)" | 证明 Pod 处于无法完成的终止状态，且持续时间极长 |
| 2 | K8s State | kubernetes | pod.condition: ContainersNotReady, phase: Running | 提供 Pod 运行时状态快照，作为 Terminating 现象的底层状态支持 |
| 3 | K8s Event | kubernetes | Killing: "Stopping container app" (54m ago) | 证实 kubelet 已在 54 分钟前尝试停止容器，说明容器本身已停止但 Pod 未结束 |
| 4 | K8s State | kubernetes | container.last_exit_code: 137 | 确认容器是以非零退出码被终止的，对应 Error 状态 |
| 5 | K8s State | kubernetes | container.last_terminated_reason: "Error" | 标记容器异常终止，是触发清理流程的初始事件 |
| 6 | K8s Event | kubernetes | 事件记录包含 Exit Code: 137 及 CNI 状态信息 | 反映资源释放过程中的网络状态残留，佐证清理流程受阻于资源级操作 |
| 7 | Metric | prometheus | restart_count: 0 | 证实异常发生后容器未重启，排除了自愈重试导致的问题 |

**证据关联说明：**
K8s State 显示 Pod 停滞在 Terminating 54 分钟，而 K8s Event 明确记录该时间点 kubelet 已完成 `Stopping container app` 的动作，随后容器以 Exit Code 137 退出。由于容器进程早已结束且未重启（Metric 确认），Pod 对象的清理被 API Server 永久挂起，这强有力地指向了 Kubernetes 对象生命周期管理器在等待特定资源（如 Finalizers）时被阻塞，而非运行时资源耗尽或网络中断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被注册了自定义 finalizer 'aiops.lab/hold' → 容器因 Error 异常终止 → API Server 发起删除请求 → 等待 finalizer 释放失败 → Pod 处于 Terminating 状态且无法删除
```

### 根因结论

**已确认的根因：** Pod `aiops-case-11/workload` 处于 Terminating 状态的根本原因是被自定义 `finalizer` (`aiops.lab/hold`) 锁定。
根据事实证据，Pod 中的 `app` 容器在 54 分钟前因 `Exit Code: 137` 错误被 kubelet 停止（证据 #3, #4），但 Pod 对象本身的删除流程卡死。在 Kubernetes 机制中，`finalizer` 会阻止 Pod 在自定义清理逻辑完成前被移除。现有证据证实了容器已死但 Pod 未删，这与 `finalizer` 未正确释放的模型完全吻合（证据 #1, #2）。

**已知未知项：** 输入事实明确指出当前未知项为“谁负责注册 'aiops.lab/hold' finalizer”以及“该 finalizer 对应的控制器逻辑为何未正确清理”。由于缺乏 Logging 和 Tracing 数据，以及未捕获到涉及该 custom finalizer 的控制器交互事件，我们无法从证据层面进一步确定是控制器宕机、逻辑 Bug 还是资源权限问题导致了清理失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.7s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-11/workload: 42.6s (Evidence 33.8s, RCA 8.7s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
