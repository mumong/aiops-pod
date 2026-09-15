## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 在容器已退出（exitCode=137）17分钟后仍保持 Terminating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `ContainersReady: False` (reason: ContainersNotReady) | 证明 Pod 处于非就绪的终止状态 |
| 2 | K8s State | Pod Status | `Terminating (lasts 17m)` | 确认卡滞现象的持续时间与核心状态 |
| 3 | K8s State | Container Exit Code | `app` 容器 `exit_code: 137` | 确认容器已因 SIGKILL 信号终止 |
| 4 | K8s State | Pod Phase | `phase: Running` | 结合 Terminating 状态，确认对象未进入 Completed 阶段 |
| 5 | K8s Event | Event | `Normal Killing`, `Stopping container app` | 记录容器被停止的操作事件 |
| 6 | Metric | kube_pod_container_status_restarts_total | `0` | 证明未发生重启，排除了重启循环 (CrashLoopBackOff) |

- 证据 1、2、3 互相印证了“容器已终止但 Pod 对象未删除”的异常状态。
- 证据 6 排除了容器重启导致 Pod 滞留的可能性。
- 现有证据仅能确认终止行为，无法确定 137 信号的确切触发源头。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了自定义 finalizer ('aiops.lab/hold') → API Server 等待最终资源清理 → 容器异常终止 (SIGKILL) → 删除流程被阻塞，Pod 长期处于 Terminating 状态
```

### 根因结论

已确认根因为 Pod 元数据中配置了 `aiops.lab/hold` 自定义 Finalizer（事实绑定引用 `fact-f6128af0681d`），该机制要求特定外部控制器完成清理工作并移除该标签后，API Server 才会完成 Pod 的删除流程。当前 Pod 中的 `app` 容器已发生退出代码 137 (SIGKILL) 事件且未重启，但外部控制器的状态未在采集范围内得到证实，导致删除操作挂起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.5s
├─ 并发证据采集: 37.1s
│  └─ g1 aiops-case-11/workload: 37.1s (Evidence 28.1s, RCA 8.9s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
