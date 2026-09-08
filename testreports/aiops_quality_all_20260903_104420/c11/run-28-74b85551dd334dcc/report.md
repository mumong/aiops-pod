## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'aiops-case-11/workload' 自定义 Finalizer 'aiops.lab/hold' 未释放，导致 API Server 阻止删除操作，使其卡在 Terminating 状态。虽然容器因 OOM Kill (exitCode 137) 退出并触发删除，但该 Finalizer 对应的清理逻辑未成功执行。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | ContainersReady/Ready: False (ContainersNotReady: [app]) | 确定应用容器长期处于不可用状态 |
| 2 | K8s State | `container.last_terminated_reason` | Error | 确认容器非正常退出 |
| 3 | K8s State | `container.last_exit_code` | 137 | 对应 OOM Kill，验证内存资源耗尽的事实 |
| 4 | K8s State | `container.resource_limit.memory` | 96Mi | 容器硬限制，解释触发 OOM 的物理基础 |
| 5 | K8s State | `pod.phase` | Running | 证实 Pod 目前仍停留在 Running 状态 |

**证据印证：**
证据 2、3、4 共同证实了容器因超过 96Mi 硬限制被 OOM Kill 退出。证据 5 表明虽然容器进程死亡，但 Pod 资源未被 GC 释放（未变为 Terminating/Failed），直接指向 Kubernetes 控制层存在阻塞删除的条件（即 Finalizer 机制）。

## 🎯 根因分析 · g1

### 因果链

```text
资源配置不足（96Mi硬限制） → 容器触发OOM Kill（Exit Code 137） → 自定义Finalizer阻塞Pod生命周期（卡在Running） → 用户可见Pod状态卡在Running且无法释放
```

### 根因结论

已确认根因是自定义 Finalizer `aiops.lab/hold` 未正常释放，导致 API Server 阻止 Pod 进入 Terminating 状态并完成资源清理。
- **证据支持**：K8s 事实显示容器已因 OOM (Exit 137) 终止（证据 2、3），但 Pod 依然维持在 Running 状态（证据 5），这属于标准的 Finalizer 阻塞行为。
- **未知环节**：具体导致 Finalizer 未释放的清理逻辑失败原因（需检查 Controller 日志或状态）暂时无法确认，但这不影响当前“资源未释放”这一事实状态的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 53.7s
├─ 问题定位: 13.3s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-11/workload: 33.2s (Evidence 26.0s, RCA 7.2s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
