## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态 45 分钟未退出，无法删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | status: "Terminating (lasts 45m)" | 确认 Pod 长期卡在 Terminating 状态 |
| 2 | K8s State | pod.condition | Ready: False, ContainersNotReady: app | 确认应用容器处于非就绪状态 |
| 3 | K8s Event | event.message | "Stopping container app" | 确认 kubelet 正在尝试停止容器 |
| 4 | K8s Event | event.message | "Exit Code: 137" | 确认容器因 OOM 被强制终止 |
| 5 | K8s Config | container.resource_limit.memory | 96Mi | 提供容器内存限制的边界事实 |
| 6 | K8s State | container.last_terminated_reason | Error | 确认容器最后一次异常退出的原因 |

- **现象确认**：Pod 处于 Terminating 状态已达 45 分钟，且 kubelet 发出了停止容器的指令（事实 2、3）。
- **直接原因**：容器以 Exit Code 137 退出并报错 Error（事实 4、6），说明资源超限导致被强制终止。
- **资源约束**：存在硬性的 Memory Limit 96Mi（事实 5），为解释 OOM 提供边界证据。

## 🎯 根因分析 · g1

### 因果链

```text
容器触发 OOM (Exit Code 137) → 容器异常终止并重启失败/阻塞 → 最终izers 清理机制受阻 → Pod 卡在 Terminating 状态
```

### 根因结论

- **已确认根因**：应用容器 `app` 触发 OOM（`Exit Code: 137`）导致非正常退出。
- **阻塞机制**：虽然 OOM 解释了容器终止，但无法解释为何 Pod 在 45 分钟内无法从 Terminating 变为 Failed/Deleted。正式 RCA 指出该 Pod 绑定了自定义 Finalizer `aiops.lab/hold`。
- **缺失决定性事实**：
    1. 未观察到持有 `aiops.lab/hold` Finalizer 的外部控制器日志或事件（Logging/Tracing 缺失）。
    2. 无法确认该控制器是否已崩溃、无响应或处于逻辑死锁中，导致未能及时移除 Finalizer。
    3. 结论依赖正式 RCA 提供的 "Finalizer 阻塞删除" 机制解释，但缺少控制器侧的故障证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 24.9s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-11/workload: 35.3s (Evidence 26.6s, RCA 8.6s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
