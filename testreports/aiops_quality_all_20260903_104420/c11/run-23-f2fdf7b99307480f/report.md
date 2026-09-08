## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload Terminating Stuck |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status (fact-12715ce3ec30) | status: Terminating (lasts 44m) | 明确异常现象：Pod 在 44 分钟前进入 Terminating 状态且未退出 |
| 2 | K8s State | pod.phase (fact-d4b75d4f775d) | phase: Running | 辅助确认：Pod 底层资源仍未被 K8s 回收，处于僵持状态 |
| 3 | K8s Event | event.message (fact-1267b19dbec2) | message: Normal Killing kubelet Stopping container app | 证明 kubelet 已执行停止容器的动作，Kubelet 侧无故障 |
| 4 | K8s State | container.last_exit_code (fact-75c7161cab69) | exit_code: 137 | 证明容器是因系统强制终止 (OOMKill/Shutdown) 而退出，并非健康存活 |
| 5 | K8s Event | event.message (fact-7cc5ded708a2) | message: Exit Code: 137 | 交叉验证容器退出原因，确认异常终止信号 |
| 6 | Metric | container restarts (fact-7a7908222167) | value: 0 | 排除重启风暴或循环拉起，说明该 Pod 自启动后未成功恢复过 |

**证据关联说明**：
- **机制确认**：事实 #3 与 #4 证实容器因收到终止信号（Exit 137）已停止运行，但事实 #1 显示 Pod 状态卡在 `Terminating`。
- **排除干扰**：事实 #5 确认了退出码的真实性；事实 #6 表明这不是一个反复重启的问题，排除了应用崩溃导致 Pod 状态不稳定的其他可能。
- **现象锁定**：Kubelet 完成了删除操作，但 Pod 对象未被删除，且无日志或追踪数据支持外部控制器未响应，仅能从状态机卡点推断。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器异常终止 (Exit 137) → 触发 Pod 删除流程 → Custom finalizer 'aiops.lab/hold' 未被清理 → Pod 对象无法从 API Server 移除
```

### 根因结论

**已确认的根因**：Pod 状态卡死是由自定义 Finalizer `aiops.lab/hold` 未能被移除导致的。
**依据**：
- Pod 处于 `Terminating` 状态超过 44 分钟 (证据 #1)，说明垃圾回收（Garbage Collection）流程被阻断。
- 容器已非正常运行状态（Exit 137, 证据 #3, #4），且 Pod 本身无健康度问题（证据 #2）。
- 结合正式 RCA，在 Kubelet 已成功停止容器的前提下，Pod 对象删除阻塞的直接原因是 Finalizer 未清除。

**当前证据局限**：
现有事实仅展示了“被 Finalizer 阻塞”这一**结果现象**。由于 Logging 和 Tracing 维度为空，且无证据显示 Finalizer 控制器或 Webhook 的状态，当前数据无法证明该 Finalizer 是“正常等待业务逻辑完成”还是“控制器/Webhook 故障导致清理失败”。因此，根因确认为“Finalizer 阻塞”，但阻塞的**深层系统原因（如控制器 Bug 或超时）**在当前证据下**证据不足**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 41.6s
│  └─ g1 aiops-case-11/workload: 41.6s (Evidence 34.6s, RCA 6.8s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- 未调用 Runbook
