## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod `aiops-case-07/workload-dff5cbc6b-kmfxx` 处于 `CrashLoopBackOff` 状态，容器 `app` 12次重启后仍失败退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason` = `CrashLoopBackOff`; `container.restart_count` = 12 | 确认应用处于崩溃重启循环中 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason` = `Error`; `container.last_exit_code` = 78 | 确认为应用层终止，非调度或基础设施问题 |
| 3 | Logging | Elasticsearch | 聚合日志模式 `CONFIG_MISSING` (HTTP 500, path `/work`)；出现 8 次；内存占用 `allocated_mib` 恒为 0 | 证实应用因配置缺失无法正常运行，且未能分配预期资源 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory` = `96Mi`; `container.resource_request.memory` = `24Mi` | 排除内存硬限制溢出导致的 OOMKilled |
| 5 | Tracing | Deepflow/Tempo | L7 Flow `/work` 请求失败 (HTTP 500, src 172.16.104.9, dst 172.16.104.15) | 证明在崩溃期间应用仍在处理请求并明确返回配置错误 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (label: reason=Error) = 1 | 验证容器非 OOMKilled 或 CrashLoopBackOff 等待状态，而是以 Error 退出 |

**证据关系说明：**
证据 1、2、6 共同确认了 `CrashLoopBackOff` 的底层原因是应用进程以 Error 状态退出（证据 2）。证据 3 和 5 提供了直接的应用层诊断事实，证明容器进程（exit code 78）在启动或处理请求时明确抛出了 `CONFIG_MISSING` 错误，而非由 K8s 调度、资源限制（证据 4）或网络故障引起。

## 🎯 根因分析 · g1

### 因果链

```text
配置文件（ConfigMap `workload-code`）挂载路径缺失或键值错误 → server.py 运行时抛出 CONFIG_MISSING 异常 → 应用进程以 Exit Code 78 退出 → Kubelet 触发 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
应用容器启动或运行失败的根本原因是**配置缺失**。证据表明应用进程在运行时无法找到预期的配置文件，从而抛出 `CONFIG_MISSING` 错误（Exit Code 78），导致 Kubernetes 认为容器异常终止并不断重启（CrashLoopBackOff）。

*   **支撑事实：** 容器最后退出代码为 78（证据 2），且 K8s Event 显示 `reason: Error`（证据 1、6）。日志明确捕获到 8 次 `CONFIG_MISSING` 错误（证据 3），Tracing 数据也记录了 `/work` 接口因同样的配置问题返回 500（证据 5）。同时，资源监控显示容器从未分配过内存（证据 3 `allocated_mib=0`），进一步排除了 OOM 或资源竞争的可能性。

*   **未确认事项：**
    由于输入事实未包含 ConfigMap `workload-code` 的实际内容与 Pod 挂载卷定义的对比数据，以下细节无法通过现有证据确认：
    1.  具体缺失的配置键名是什么？
    2.  是 ConfigMap `workload-code` 内容本身缺失键值，还是 Pod 的 VolumeMount 配置路径错误导致文件未挂载到正确位置？

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.0s
├─ 并发证据采集: 68.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 68.3s (Evidence 56.4s, RCA 11.7s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
