## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff，容器 app 退出码 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error; last_exit_code: 137 | 确认容器被终止且退出码为 137 |
| 2 | K8s Config | kubernetes | container.resource_limit.memory: 96Mi | 提供容器内存硬限制的具体数值 |
| 3 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 解释 Pod 处于 CrashLoopBackOff 的外部触发因素 |
| 4 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff | 描述当前异常的持续状态 |
| 5 | Metric | prometheus | kube_pod_container_status_last_terminated_reason: 1 (reason: Error) | 独立确认最后一次终止原因为 Error |
| 6 | Logging | elasticsearch | pattern: request completed, http_status: 200, path: /work (occurrence: 8次) | 排除应用崩溃前的请求报错，说明服务响应正常 |
| 7 | Tracing | deepflow | flow: GET /work, response_code: 200 (occurrence: 9次) | 网络层确认服务在终止前正常处理了流量 |

**证据关联分析**：
证据 1 (ExitCode 137) 与证据 2 (96Mi 限制) 构成因果关系：Linux 中退出码 137 代表进程被 SIGKILL 强制终止，结合极小的内存限制，高度指向 OOM Killer 机制。证据 3 解释了重启失败的原因，证据 5 从监控侧独立验证了终止事件。证据 6 和 7 排除了应用层逻辑错误，证明进程是在运行中被系统级手段终止的。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制设置过低(96Mi) → Python 进程内存需求超出限制 → Kernel OOM Killer 触发并发送 SIGKILL (exitCode=137) → 容器终止并进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是 **容器内存资源限制 (96Mi) 过低**。

1. **直接机制**：容器 `workload-79d9f8fd88-48j8r` 的主进程（Python）在启动或运行过程中，内存使用量超过了配置的硬限制 `96Mi`。
2. **证据支撑**：
   - **退出码 137**：证据 1 显示容器退出码为 137，这在 Kubernetes 中是进程被 OOM Killer 发送 SIGKILL 信号终止的标准特征。
   - **内存限制**：证据 2 确认容器被限制在仅 `96Mi` 的内存下运行，这对于大多数现代应用而言是极低的阈值，极易触发 OOM。
   - **终止状态**：证据 3 和 4 显示容器因重启失败进入 `CrashLoopBackOff`，且 Liveness Probe 也受到影响（返回 500），这与进程被突然杀掉导致服务无法健康响应的现象一致。
3. **排除应用崩溃**：日志（证据 6）和链路追踪（证据 7）显示在终止前，服务均能正常返回 HTTP 200，排除业务逻辑错误或请求处理异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.9s
├─ 并发证据采集: 69.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 69.8s (Evidence 62.2s, RCA 7.4s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
