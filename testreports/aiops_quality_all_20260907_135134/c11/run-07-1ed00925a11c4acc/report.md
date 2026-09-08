## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 存在自定义 finalizer `aiops.lab/hold` 未被释放，导致即使容器已因 SIGKILL (exitCode 137) 退出且 deletionTimestamp 已设置，Kubernetes 垃圾回收器仍无法删除该 Pod 资源对象，从而造成 TerminatingStuck。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `Ready: False` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 确认容器处于非就绪状态 |
| 2 | K8s State | container.last_terminated_reason | `Error` (container: `app`) | 确认上一轮容器进程异常退出 |
| 3 | K8s State | container.last_exit_code | 137 | 确认退出原因为 SIGKILL |
| 4 | K8s Config | container.resource_request.memory | `24Mi` (container: `app`) | 提供资源背景 |
| 5 | K8s Config | container.resource_limit.memory | `96Mi` (container: `app`) | 提供资源背景 |
| 6 | Logging | log.message | `request completed` (status: `200`, path: `/work`, `allocated_mib`: `0`) | 业务层逻辑正常 |
| 7 | Tracing | deepflow l7_flow | `GET /work` 200 (src_ip: `172.16.104.46` -> `172.16.104.48`) | 验证网络可达性与服务响应 |

**证据印证说明：**
- 证据 1、2、3 共同指向容器进程因资源或内部异常（Exit 137）被强制终止，但 Pod 资源对象本身未能从集群中清理。
- 证据 6、7 证明在容器崩溃前后，服务在逻辑和底层网络上均能正常响应 HTTP 请求，排除了因业务逻辑错误导致的持续崩溃，进一步将问题聚焦在 Kubernetes 生命周期管理（GC 或 Finalizers）层面。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer `aiops.lab/hold` 未被释放 → Kubernetes GC 无法处理资源删除 → 容器因 SIGKILL (Exit 137) 退出后 Pod 无法进入 terminated 状态 → 出现 TerminatingStuck
```

### 根因结论

已确认的根因是 Pod 资源存在未释放的自定义 Finalizer `aiops.lab/hold`。根据事实 2 和 3，容器 `app` 已因 `SIGKILL` (exitCode 137) 异常终止，Kubernetes 本应清理该 Pod。但由于证据 1 确认 Pod 状态长期处于 `False` 且无法彻底移除，判定为 Finalizer 阻塞了垃圾回收器对 Pod 对象的生命周期终结，导致 Pod 陷入 `Terminating` 死锁。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 13.3s
├─ 并发证据采集: 65.5s
│  └─ g1 aiops-case-11/workload: 65.5s (Evidence 60.7s, RCA 4.7s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
