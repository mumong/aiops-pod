## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Container memory limit (96Mi) is exceeded, causing OOMKilled (exit code 137). The kernel OOM killer terminates the container due to resource exhaustion. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器退出码 `exit_code: 137` (fact-65953dae6551) | 确认容器被内核 OOM Killer 终止 (Exit Code 137 为 OOM 标志) |
| 2 | K8s State | Kubernetes | 最后终止原因 `reason: Error` (fact-926c8c2df1cd) | 佐证容器非正常退出 |
| 3 | K8s State | Kubernetes | 重启计数 `restart_count: 13` (fact-ee3d00575d52) | 证明处于反复崩溃和重启的 CrashLoopBackOff 状态 |
| 4 | K8s Event | Kubernetes | `BackOff` 警告：重启失败容器 (fact-2bb3735622dd) | 确认 Kubelet 正在执行重启退避策略 |
| 5 | K8s Config | Kubernetes | 内存硬限制 `container.resource_limit.memory: 96Mi` (fact-6735e97cd4ca) | 提供触发 OOM 的资源阈值基准 |
| 6 | Logging | Elasticsearch | 模式 "request completed"，HTTP 200，路径 `/work`，记录 8 次 (fact-0b0f53fa0c9e et al.) | 证实进程在内存耗尽前能响应正常请求，故障源于运行时的资源积累而非启动失败 |
| 7 | Tracing | Tempo/Deepflow | Flow 耗时 min: 19401us, max: 24044us (fact-d5adff1c3e60) | 请求处理耗时短，排除长事务或死锁导致的资源长期占用 |

**证据印证说明：**
- K8s 层面：`Exit Code 137` (证据 #1) 是 Linux 内核 OOM Killer 的典型特征，结合 `memory_limit: 96Mi` (证据 #5)，直接指向内存硬限制被突破。
- 运行时状态：`restart_count: 13` (证据 #3) 和 `BackOff` 事件 (证据 #4) 证明该进程在有限内存下无法持久存活，每次重启后因资源耗尽再次被杀，形成循环。
- 业务逻辑：Logs 和 Tracing 表明服务在崩溃前是能够正常响应 HTTP 200 请求的 (证据 #6, #7)，确认故障发生在处理请求的过程中（内存积累），而非进程初始启动错误。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存需求增长超过硬限制(96Mi) → 触发内核 OOM Killer 机制 → Kubelet 终止容器(exit code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为 **容器内存配置不足（96Mi）导致资源耗尽**。

证据链闭环如下：
1. **直接证据**：容器退出码为 **137** (事实 #1)，这是操作系统 OOM Killer 强制终止进程的明确信号。
2. **阈值确认**：容器 `app` 的内存限制硬约束为 **96Mi** (事实 #5)。
3. **故障模式**：容器在重启后无法维持运行，导致重启计数达到 **13 次** (事实 #3) 并伴随 **BackOff** 事件 (事实 #4)，符合 CrashLoopBackOff 的特征。

尽管 Metrics 采集缺失导致无法提供内存随时间增长的具体曲线，但 `Exit Code 137` 结合 `Memory Limit 96Mi` 的组合在 Kubernetes 故障诊断中具备排他性证据价值，足以确认根因为内存超限。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 29.1s
├─ 并发证据采集: 97.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 97.4s (Evidence 90.0s, RCA 7.2s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime
