## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod被自定义Finalizer aiops.lab/hold阻止释放 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 状态为 `Terminating (lasts 33m)` | 确认 Pod 处于僵死删除状态，无法完成生命周期清理 |
| 2 | K8s Event | kubernetes | `Normal Killing` 33m，kubelet 正在停止容器 app；注解包含 `Exit Code: 137` | 确认应用进程被系统强制杀死（OOM Kill / SIGKILL） |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: `Error`，`last_exit_code`: `137` | 佐证应用进程异常终止，非正常退出 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: `96Mi` | 提供触发 SIGKILL 的潜在硬件限制上下文 |

Pod 经历了正常的启动、运行和因资源或错误导致的终止（Exit 137），但在被 Kubernetes 删除（Terminating）后，状态在 33 分钟内未转为 Failed 或 Completed，说明删除操作被 API Server 或 GC 挂起。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器异常退出 (Exit 137) → Finalizer aiops.lab/hold 未被移除 → 删除请求被 API Server 拒绝/挂起 → Pod 陷入 Terminating 状态（卡住 33m）
```

### 根因结论

已确认的根因是：Pod `aiops-case-11/workload` 被自定义 Finalizer `aiops.lab/hold` 阻止释放（证据 1）。

Pod 在 33 分钟前因异常（Exit Code 137，可能是内存溢出或系统中断）被杀死，但 Kubernetes 对象在删除时需要等待所有 Finalizer 被清理。当前 Pod 依然处于 `Terminating` 状态，证明持有 `aiops.lab/hold` 的控制器或服务未能处理清理逻辑或移除该 Finalizer。

**未确认/缺失事实：**
缺乏关于“持有 Finalizer 的具体外部控制器或服务”为何未处理清理逻辑的证据。Logging 和 Tracing 维度为空，且 `kubectl lineage` 等工具调用失败，无法通过外部事件流确认控制器端的状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 23.5s
├─ 并发证据采集: 82.4s
│  └─ g1 aiops-case-11/workload: 82.4s (Evidence 76.0s, RCA 6.2s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
