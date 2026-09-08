## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 存在自定义 finalizer `aiops.lab/hold` 阻塞删除流程，导致 Pod 进入 Terminating 状态后无法彻底清理。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `ContainersReady`: False, `ContainersNotReady: app`; `Ready`: False | 证实容器未能通过就绪探针或状态检查，属于 Pod 运行异常的明确症状 |
| 2 | K8s State | Container Exit Code | `container: app`, `exit_code`: 137 | 进程被系统强制终止（SIGKILL），通常由内存超限触发 |
| 3 | K8s Config | Resource Limit | `container: app`, `memory`: 96Mi | 容器设置了极小的内存上限，与上述强制终止（OOM Kill）高度吻合 |
| 4 | K8s State | Pod Phase | `phase`: Running | Pod 依然处于 Running 阶段，说明虽然容器退出异常，但尚未被触发清理 |

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制过小 (96Mi) → 运行中触发系统 OOM Kill (Exit Code 137) → 容器进入非就绪状态 (ContainersNotReady) → Pod 处于异常 Running 状态
```

### 根因结论

- 已确认根因：容器 `app` 因内存限制过低（96Mi）触发 OOM Kill，导致退出码为 137 且未进入就绪状态 [证据 2, 3, 1]。
- 证据不足：诊断仅能确认为资源限制导致的进程异常退出，无法仅凭现有 K8s 状态确认是否存在导致内存飙升的代码级缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 58.9s
├─ 问题定位: 16.5s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-11/workload: 36.7s (Evidence 31.8s, RCA 4.9s)
└─ 汇总总结: 5.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
