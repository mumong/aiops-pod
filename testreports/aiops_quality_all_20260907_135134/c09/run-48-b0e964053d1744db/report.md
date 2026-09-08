## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用服务依赖缺失导致健康检查持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Ready=False (ContainersNotReady), ContainersReady=False (ContainersNotReady) [fact-799a63fcfc0b, fact-cd7805dee440, fact-d8180a76f49d] | 确认容器已运行 (Running) 但处于未就绪状态，触发健康检查 |
| 2 | K8s Event | kubernetes | Warning Unhealthy: Readiness probe failed: HTTP probe failed with statuscode: 503 [fact-a2b3ef43c1b7] | 直接证实健康检查失败的现象及 HTTP 状态码 |
| 3 | Logging | elasticsearch | pattern: "dependency unavailable", http_status: 503, path: "/work", level: error (发生 8 次, 04:24:11 ~ 04:24:57) [fact-7500ca1ea7f4, fact-7198fa4b8839, fact-17d29e62f8d1, fact-4f3ba1026671, fact-638ba8355027, fact-23148e6228bf, fact-2379b3b22ec2, fact-6af79fb8fc67] | 揭示应用内部处理请求时遇到依赖缺失并返回 503 状态 |
| 4 | Tracing | deepflow | flow: GET /work -> 172.16.104.35:503, src_ip: 172.16.104.55 (重复 9 次, 04:24:11 ~ 04:49:17) [fact-021519f42c11, fact-3a794b9f1c84, fact-3811f477cd49, fact-502fd2fcb23b, fact-3403cdc08325, fact-163d164a9dd6, fact-04d954117e5e, fact-7badb0729607, fact-6dca8968e3aa] | 确认客户端（IP .55）持续向 Pod（IP .35）的 /work 端点发送请求并获得 503 响应 |
| 5 | Tracing | tempo | span: GET /work -> 503 (trace_id: 6f6bdf0cfdfd482b9d037f0ef4321493) [fact-114ca8885591] | 补充单次特定请求的 Trace 视图，状态码与日志/Flow 一致 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total = 0 [fact-eb3995b3f397] | 确认应用未发生进程崩溃或重启，故障属于逻辑/依赖层面的连续失败 |

**证据关联说明：**
- Pod 状态（事实1）与 K8s 事件（事实2）印证了 kubelet 检测到应用端点响应 503。
- 日志（事实3）、Deepflow Flow（事实4）和 Tempo Span（事实5）在 HTTP 状态码（503）、请求路径（/work）和发生时间上高度一致，形成闭环证据链。
- Deepflow Flow（事实4）明确指出源 IP 为 172.16.104.55 的客户端正在重试请求，确认了 503 的持续性来源；Metric（事实6）排除了因 OOM 或 CrashLoop 导致的服务中断可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务存在依赖缺失 → 健康检查探针（GET /work）请求被应用拒绝（返回503） → Pod Readiness 状态变为 False → 集群将该 Pod 标记为未就绪且不接收流量
```

### 根因结论

已确认的根因为**应用服务依赖缺失**。

当前证据链完整支撑该结论：
1. **直接症状**：Pod 状态显示 `Ready=False`，且 K8s 事件明确指出 Readiness 探针因 `statuscode: 503` 而失败（证据 1, 2）。
2. **根本机制**：应用侧日志明确记录了错误模式为 `dependency unavailable`，且返回了 `http_status: 503`（证据 3）。
3. **外部验证**：网络流量日志（Deepflow）证实来自集群内部（172.16.104.55）的请求持续遭遇 503 拒绝（证据 4），且应用未发生重启（证据 6），表明应用进程存活但功能不可用。

综上，Pod 处于 Running 状态但因应用逻辑错误导致健康检查持续失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 19.2s
├─ 并发证据采集: 75.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 75.9s (Evidence 69.8s, RCA 5.9s)
└─ 汇总总结: 16.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed, pod-config-error
