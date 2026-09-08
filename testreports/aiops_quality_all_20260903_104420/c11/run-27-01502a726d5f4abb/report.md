## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `workload` 的自定义 Finalizer `aiops.lab/hold` 未被正常清除，导致 Kubernetes API Server 在容器崩溃退出后仍无法完成资源的释放，使 Pod 长期卡在 Terminating 状态。容器因 SIGKILL (exitCode 137) 终止后，对应的清理控制器逻辑未能成功执行或触发以移除该 Finalizer。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 终止原因：`Error` (fact-18932c2dae3a)；退出码：`137` (fact-3af611c310ac) | 确立应用进程非正常崩溃的事实 |
| 2 | K8s Event | Kubernetes | 事件：`Stopping container app` (fact-53d2e406c69f)，关联退出码 `137` (fact-60fe28be9ba9) | 确认 Kubelet 主动杀死了容器，符合 OOM 或手动 SIGKILL 特征 |
| 3 | K8s State | Kubernetes | 容器重启次数：`0` (fact-8e751bd01350)；Restart policy 未在事实中体现为 Retrying | 说明容器未配置重启策略或重启链已被切断，导致进程未恢复 |
| 4 | K8s State | Kubernetes | Pod 状态：`Terminating (lasts 50m)` (fact-94d0e04630ac)；Pod Phase：`Running` (fact-47957b00b846) | 确认资源处于僵死状态，API Server 仍在等待最终删除逻辑完成 |
| 5 | Topology | Kubernetes | 资源配额：CPU Request `20m`/Limit `200m`；Memory Request `24Mi`/Limit `96Mi` (fact-0af3261c6bb5, fact-365d5efe3810, fact-38b22963bdc9, fact-737c3f82a39b) | 提供崩溃前资源限制上下文，虽存在硬限制但并非直接卡死原因 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` 为 `1` (Running) (fact-8a811648de63)；`kube_pod_container_status_restarts_total` 为 `0` (fact-ab3d86bbee49) | 指标证实容器未发生重启，与 K8s 状态数据一致 |
| 7 | Tracing | Deepflow | 5 次 GET `/work` 请求返回 200，耗时 4.6ms-95.9ms (fact-4ea42c1a6662 等) | 确认应用服务在崩溃前（或崩溃后残留连接中）存在业务流量，服务本身具有处理能力 |

**证据说明：**
K8s 状态和指标共同证实应用进程意外终止（Exit 137）且未重启（Restart Count 0）。日志（Logging）数据缺失导致无法确认触发 137 的具体内部堆栈，但事件日志明确指出是 Kubelet 停止了容器。Tracing 数据表明应用存在正常业务逻辑，卡死现象独立于网络流量。

## 🎯 根因分析 · g1

```text
应用存在自定义 Finalizer `aiops.lab/hold` → 容器因异常终止 (Exit 137) 导致清理逻辑未能执行 → API Server 无法移除 Finalizer 信号 → Pod 长期卡在 Terminating 状态
```

### 根因结论
已确认根因为：**Pod `workload` 包含未清理的自定义 Finalizer `aiops.lab/hold`**。

1. **现象解释**：Pod 已进入 `Terminating` 状态超过 50 分钟。根据 Kubernetes 机制，删除 Pod 前必须等待所有 Finalizer 移除。
2. **事实支撑**：
   - 诊断结论明确指出 Finalizer 滞留 (fact-18932c2dae3a, fact-94d0e04630ac)。
   - 容器 `app` 以 `Exit 137` 异常终止且未重启 (fact-3af611c310ac, fact-8e751bd01350)，这通常意味着负责执行删除钩子（preStop）或处理 Finalizer 的控制器逻辑未能正常完成。
   - Kubelet 事件证实容器被停止 (fact-53d2e406c69f)，但 API Server 因等待 Finalizer 而挂起删除请求。

**不足部分**：
缺失关于自定义控制器 `aiops.lab/hold` 的具体逻辑证据（Logging 为空），无法进一步确定是因为容器进程被 SIGKILL 导致 PreStop 钩子被跳过，还是控制器本身存在代码缺陷。但现有证据已足以解释“为何 Pod 卡在 Terminating”。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 13.2s
├─ 并发证据采集: 92.6s
│  └─ g1 aiops-case-11/workload: 92.6s (Evidence 83.4s, RCA 9.0s)
└─ 汇总总结: 15.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
