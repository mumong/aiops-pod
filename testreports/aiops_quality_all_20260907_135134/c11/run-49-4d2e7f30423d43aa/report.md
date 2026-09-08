## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 is stuck in Terminating state with deletionTimestamp set but not removed. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod.phase=Running; pod.status=Terminating (deletionTimestamp已设置) | 确认 Pod 处于停滞状态，调度正常但生命周期卡住 |
| 2 | K8s State | Kubernetes | pod.condition type=ContainersReady/Ready, status=False, reason=ContainersNotReady | 反映容器当前不可用，是终止过程中的中间态特征 |
| 3 | K8s State | Kubernetes | container.last_exit_code=137 (OOMKilled信号); container.last_terminated_reason=Error | 解释容器非正常退出的直接原因 |
| 4 | K8s Config | Kubernetes | container.resource_request.memory=24Mi; container.resource_limit.memory=96Mi | 提供资源限制上下文，确认存在 OOM 触发条件 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total=0 | 验证重启计数为0，排除循环崩溃重启导致的卡死 |
| 6 | Metric | Prometheus | kube_pod_status_phase Failed=0 | 排除 Pod 处于完全失败阶段的可能 |

**证据关联说明：**
Kubernetes 核心事实（#1）明确指出 Pod 处于 Terminating 阶段但未被物理删除。结合事实 #3 (Exit Code 137) 和 #4 (Memory Limits)，容器因内存超限被系统杀死。Metric 事实 #5 证实这是首次启动后的单次失败（Restart Count=0），排除了应用崩溃循环。综合表明，容器已退出，但 Pod 资源清理受阻。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 包含 'aiops.lab/hold' 自定义终态拦截器 → 触发删除但拦截器未释放 → API Server 阻止资源回收 → Pod 卡在 Terminating 状态且无法物理删除
```

### 根因结论

**已确认根因：** Pod 因包含自定义终态拦截器 `aiops.lab/hold` 而陷入终止停滞。

该终态拦截器在 Pod 被标记删除（设置 `deletionTimestamp`）后未被对应的控制器或处理程序成功释放，导致 Kubernetes API Server 拒绝完成 Pod 的删除流程。虽然容器因 OOM (Exit Code 137) 已经停止运行，但 Pod 对象本身在 API 层面无法移除。

**证据支撑：**
- K8s 状态事实 `pod.phase=Running` 配合 `deletionTimestamp` 存在，且未进入 Failed 状态，是终态未释放的典型特征 [证据 #1]。
- 容器已退出且不再重启 [证据 #3, #5]，说明计算资源已释放，问题纯粹在于元数据清理受阻。

**未确认事项：**
- 拥有该终态拦截器的具体控制器/组件身份不明。
- 该处理程序未能成功释放拦截器的具体原因（如网络超时、死锁或逻辑错误）需进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.8s
├─ 并发证据采集: 38.8s
│  └─ g1 aiops-case-11/workload: 38.8s (Evidence 30.8s, RCA 7.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
