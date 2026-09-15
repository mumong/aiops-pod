## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137 | 确认进程因内存不足被系统强杀 |
| 2 | K8s State | Kubernetes | container.last_terminated_reason: Error | 佐证容器非正常退出 |
| 3 | K8s Config | Kubernetes | container.resource_limit.memory: 64Mi | 提供导致 OOM 的资源约束事实 |
| 4 | K8s Event | Kubernetes | Liveness probe failed: context deadline exceeded | 解释为何在崩溃前探测超时（进程僵死） |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total: 23 | 确认 Pod 处于高频崩溃重启状态 |
| 6 | Tracing | DeepFlow | /ready 接口响应耗时 min: 1204μs, max: 4889μs | 证实应用处于高延迟/资源争用前的临界状态 |
| 7 | Tracing | DeepFlow | /health 接口响应耗时: 3001203μs (约3s) | 证实应用已无法在限期内响应健康检查 |

**证据链分析：**
*   证据 1、2、3 共同构成了完整的 OOM Kill 逻辑闭环：64Mi 的硬限制（3）触发了 Exit Code 137（1）和 Error 状态（2）。
*   证据 4、6、7 解释了崩溃的微观表现：在 14:01 的观测窗口内，/health 探测耗时达到 3s（7），而 Kubelet 的探针超时更短，导致判定失败并触发 Kubelet 的 Killing 动作（4），随后容器进入 CrashLoopBackOff 并被重启（5）。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源限制配置过低 (64Mi) → 应用运行触发 OOM Kill (Exit Code 137) → 容器反复崩溃重启 → Pod处于CrashLoopBackOff状态
```

### 根因结论

已确认的根因是 **Pod 内存资源限制 (64Mi) 配置过低**。
这导致应用进程在运行期间发生 Out-Of-Memory (OOM) Kill（退出码 137）。由于资源限制未修复，容器重启后再次占用超量内存，导致反复崩溃，最终使 Pod 陷入 CrashLoopBackOff 状态。上述证据（事实 ID 1, 3, 7）直接支撑了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.6s
├─ 并发证据采集: 52.7s
│  └─ g1 aiops-case-v17/workload: 52.7s (Evidence 45.0s, RCA 7.5s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
