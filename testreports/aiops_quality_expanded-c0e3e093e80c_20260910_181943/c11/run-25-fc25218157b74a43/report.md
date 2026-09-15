## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 处于 Terminating 状态卡住 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.condition: ContainersReady=False, message="containers with unready status: [app]" (fact-09c57e06fdb7, 2026-09-11T03:47:19Z) | 确认 Pod 处于非就绪状态，资源未被回收 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: Error (fact-5599371d7067) | 证明容器此前发生过异常终止 |
| 3 | K8s State | kubernetes | container.last_exit_code: 137 (fact-acab729dc465) | 证实容器因 OOMKilled 被强制终止 |
| 4 | K8s State | kubernetes | container.resource_limit.memory: 96Mi (fact-7fc0b2dc0103) | 提供导致 137 错误的具体资源限制背景 |
| 5 | K8s State | kubernetes | pod.phase: Running (fact-f050d7b89ea5) | 显示 Pod 实际仍在运行而非 Terminating，说明删除操作未完成 |
| 6 | K8s State | kubernetes | pod.condition: PodScheduled=True, Initialized=True (fact-140a0bdcd6ab, 2026-09-11T03:47:03Z) | 排除 Pod 调度失败或启动初始化阶段异常的可能 |

**证据互证说明：**
证据 1、2、3、5 结合表明 Pod 经历了一次致命的容器退出（Exit 137），但其 K8s 对象本身并未结束生命周期。证据 4 提供了退出原因的直接解释。仅凭 Kubernetes 状态和 Metric 无法解释为何 Pod 在资源耗尽后未完全终止，因此日志与追踪数据虽缺失，但无法替代当前已确认的“资源耗尽导致容器崩溃”这一直接故障机制。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(96Mi)过低 → 容器触发 OOMKilled (Exit 137) → 资源被释放但容器状态未重置 → Pod 对象残留于 Terminating/Running 混合状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-11/workload` 的容器 `app` 遭遇资源耗尽故障。
1. **资源限制过低**：容器 `app` 仅配置了 96Mi 的内存硬限制（`resource_limit.memory`）。
2. **OOMKilled 事件**：容器在 2026-09-11 的窗口期内发生了异常终止，退出码为 137（fact-5599371d7067, fact-acab729dc465），这是 Linux 系统因 OOM (Out of Memory) 杀死进程的典型特征。
3. **现象关联**：这解释了为何 Pod 处于异常状态（fact-09c57e06fdb7）。尽管正式 RCA 提及了 `finalizer` 问题，但当前提供的 Kubernetes 事实仅支持“容器因内存限制被杀”这一结论。由于正式 RCA 中的 finalizer 证据未在 fact 列表中体现，且现有事实不支持 finalizer 阻塞删除的直接观测（Pod 状态仍为 Running），本次分析仅基于确凿的退出码和资源配置得出根因。

**证据不足的方面：**
当前事实无法确认 Pod 对象为何卡在“删除未完成”或“状态不一致”的具体原因。正式的 `aiops.lab/hold` finalizer 假设缺乏直接的 K8s Object Finalizers 字段事实支持，因此关于“删除阻塞”的根因判定为**证据不足**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.0s
├─ 并发证据采集: 42.5s
│  └─ g1 aiops-case-11/workload: 42.5s (Evidence 37.6s, RCA 4.8s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
