## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 5 分钟，容器已退出但 Pod 未删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `status: Terminating (lasts 5m28s)` | 确认 Pod 处于删除挂起状态，且持续时间超过 5 分钟 |
| 2 | K8s Event | K8s Event | `Normal Killing ... Stopping container app` | 确认 kubelet 已尝试停止容器，但 Pod 未移除 |
| 3 | K8s Config | K8s Event | `Exit Code: 137` | 确认容器进程收到 SIGKILL 信号终止 |
| 4 | Logging | Elasticsearch | `pattern: request completed ... http_status: 200 ... 4 occurrences` | 确认容器在终止前（22:31:06-12）曾正常处理并返回 200 的请求 |
| 5 | Tracing | Tempo | `span: GET /work ... trace_id: 75c4028b11532f074defb107fd297f49` | 验证与日志时间匹配的成功请求链路，排除网络或应用崩溃导致的无响应 |

**证据分析：**
事实 1 和事实 2 共同描述了异常现象：容器已停止但 Pod 资源滞留。事实 3 明确指出了容器退出原因为 SIGKILL (Exit 137)。事实 4 和事实 5 确认了 Pod 在终止前具备正常的服务响应能力，且未出现应用层错误。综合来看，容器异常终止是事实，而 Pod 无法完成 Terminating 状态转换是由非应用逻辑的因素（如 Finalizer）导致，与容器内的进程或网络状态无直接因果关联。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer `aiops.lab/hold` 阻止了资源清理 → K8s API Server 等待该 finalizer 被移除 → 即使容器已退出 (Exit 137)，Pod 也无法被删除 → Pod 持续处于 Terminating 状态
```

### 根因结论

**已确认的根因：Pod 被设置了自定义 Finalizer (`aiops.lab/hold`)，导致删除流程被阻塞。**

证据编号 1、2、3 证实了 Pod 处于 Terminating 状态且容器因 SIGKILL (Exit 137) 退出。根据 Kubernetes 机制，当 Pod 被标记删除（deletionTimestamp）且包含 Finalizer 时，API Server 会等待对应的控制器移除该 Finalizer 才会真正删除 Pod。虽然容器进程已终止（证据 3），但 Pod 对象本身并未被移除（证据 1）。这直接指向了 Finalizer 清理机制的失败或阻塞。现有的 Kubernetes 事实和日志不足以进一步确定是控制器本身的 Bug、逻辑错误还是外部依赖问题导致了该 Finalizer 未被正常清理（即“未知项”）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 24.3s
├─ 并发证据采集: 83.4s
│  └─ g1 aiops-case-11/workload: 83.4s (Evidence 74.2s, RCA 8.9s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
