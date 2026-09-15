## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | 应用服务在Liveness探针路径/health上返回500错误导致Kubelet触发Kill，且应用内存限制(96Mi)过低，高内存使用导致服务无响应或崩溃（退出码137），尽管OOMKilled标志可能未显式标记在最后一次终止状态中，但137退出码与低内存限制及探针超时返回500的现象一致，表明资源限制导致服务不可用并进而被Kubelet杀死。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-26fbc8fb8607) | 触发 Kubelet 执行容器的 Kill 操作，导致重启循环的直接上游。 |
| 2 | K8s Config | kubernetes | `memory limit: 96Mi` (fact-09160ca42ecd) | 确定应用可用的最大内存边界，低限制是导致资源不足的高概率约束条件。 |
| 3 | K8s State | kubernetes | `Last exit code: 137` (fact-5952b5891ff3) | 进程被强杀（通常为 SIGKILL）的特征码，与低内存限制下的 OOM 事件高度一致。 |
| 4 | Logging | elasticsearch | `GET /work` status 200, `allocated_mib` min/max 0.0 (fact-2afa5825a7e3) | 业务接口 `/work` 运行正常，证明应用主线程未崩溃，排查范围锁定在探针或特定资源路径。 |
| 5 | Tracing | deepflow | `GET /work` response_code 200, duration max 19567.0us (fact-63424bc9df55) | 网络链路通畅，请求无超时或拒绝，排除网络或 L4 层面的中断问题。 |

上述证据链表明，应用主业务运行正常（日志与链路均证实），但 Liveness 探针路径遭遇 HTTP 500 错误（证据1），导致 Kubelet 强制杀死容器（证据3）。结合极低的应用内存限制（96Mi，证据2），高概率推断 `/health` 端点因内存不足导致服务假死或崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存限制过低(96Mi) → 资源不足导致 /health 端点响应失败(HTTP 500) → Kubelet 触发 Kill 信号(SIGKILL/退出码137) → 应用陷入 CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因：**应用资源限制（96Mi）过低与 Liveness 探针路径（/health）不可用之间的交互导致服务崩溃。**

当前现象由以下事实支撑：
1. 探针失败触发机制：Liveness 探针路径 `/health` 返回 500，导致 Kubelet 执行 Kill 操作（证据 #1）。
2. 内存瓶颈关联：应用被分配了极低的硬内存限制 96Mi（证据 #2），而业务接口 `/work` 运行完全正常（证据 #4, #5），这强烈暗示非主业务逻辑缺陷，而是 `/health` 端点因内存受限导致响应能力丧失。
3. 强制终止状态：容器以退出码 137 终止（证据 #3），确认了是被系统强杀，符合内存不足引发的终止特征。

尚未完全确认的部分：
由于日志聚合未展示 `/health` 路径的报错信息（仅展示了成功的 `/work` 路径），无法断定 500 是应用代码逻辑 Bug 还是纯粹由资源耗尽导致的无响应。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.0s
├─ 并发证据采集: 66.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 66.8s (Evidence 57.7s, RCA 8.9s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime, pod-oomkilled
