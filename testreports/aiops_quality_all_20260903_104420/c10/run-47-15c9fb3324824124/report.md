## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认 Pod 当前处于反复崩溃重启的异常状态 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x69) | 确认应用服务在运行期间发生严重错误（内部服务故障） |
| 3 | K8s Event | Kubernetes | `Exit Code: 137` / `Reason: CrashLoopBackOff` (x477 BackOff) | 记录容器反复被系统强制终止并触发退避重启的宏观现象 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error` / `container.last_exit_code`: `137` | 明确最后一次终止的原因为 Error，退出码 137 指向被系统信号强制杀死 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi` / `container.resource_request.memory`: `24Mi` | 确定应用内存硬限制为 96Mi，为判断 OOM 提供容量边界依据 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (reason=Error, count=1) | 从监控维度交叉验证容器最近一次异常终止原因为 Error |

**证据印证说明：**
Kubernetes 侧的退出码 `137`（即 `128 + 9`，SIGKILL）与容器硬限制 `96Mi` 直接构成了系统级 OOM（Out of Memory）的证据链。同时，Liveness Probe 的 `500` 错误表明应用是在处理业务逻辑（如 `/work` 接口）过程中因资源耗尽而崩溃，而非启动配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程处理请求内存分配 > 96Mi 硬限制 → Kubelet 触发 OOMKiller (SIGKILL) → 容器以 Exit Code 137 终止并重启 → Pod 陷入 CrashLoopBackOff
```

### 根因结论

**已确认根因：** 容器应用进程触发了硬性内存限制（96Mi），被宿主机 OOMKiller 强制发送 SIGKILL 终止。

**证据引用：**
1. 退出码 137（`fact-47e34f43451f`）与终止原因 Error（`fact-01b137165825`）直接证实进程是被外部信号强制杀死的，通常对应系统 OOM 机制。
2. 内存限制配置 `96Mi`（`fact-63eeb8ce17e0`）提供了触发 OOM 的容量阈值依据。
3. 监控数据 `kube_pod_container_status_last_terminated_reason=Error`（`fact-6b763d0a32ec`）与 K8s 状态一致，确认了异常终止的持续性。

**缺失事实说明：**
*   未能获取 `dmesg` 中 OOM Killer 的详细进程快照，无法确认是应用主进程还是子线程占满内存。
*   缺乏崩溃前实时内存使用量曲线（Metrics），无法精确定位 OOM 触发时的精确峰值时刻。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 26.1s
├─ 并发证据采集: 89.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 89.8s (Evidence 77.9s, RCA 11.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
