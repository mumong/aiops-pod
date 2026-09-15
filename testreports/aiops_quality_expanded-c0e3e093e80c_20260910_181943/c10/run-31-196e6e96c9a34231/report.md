## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIPs: 172.16.104.34/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod Phase: Running, Container Waiting: CrashLoopBackOff, Last Terminated Reason: Error (fact-27f1ca347506, fact-638ce0bb7931) | 确认 Pod 已启动并反复崩溃，直接症状 |
| 2 | K8s State | Kubernetes | Container Exit Code: 137 (fact-638ce0bb7931) | 指向进程异常终止，常见原因为 OOM Kill 或强制 SIGKILL |
| 3 | K8s Config | Kubernetes | Memory Limit: 96Mi (fact-002755fe8ab1), Memory Request: 24Mi (fact-4d2d59d6af17) | 资源限制极小，存在极高的 OOM 风险（上下文） |
| 4 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (fact-b0505a2ca4ba) | 存活探针因业务应用报错而失败，触发重启机制 |
| 5 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason=1 (Reason: Error) (fact-56b7dc1b4c64), restarts=13 (fact-1828c6d33084) | 量化重启频率与终止状态，确认异常已持续一段时间 |
| 6 | Logging | Elasticsearch | Pattern: request completed, http_status: 200, path: /work (fact-49d577d387f6) | 业务接口 `/work` 响应正常，证明应用核心功能仍在服务 |
| 7 | Tracing | Tempo/Deepflow | Span/Flow: GET /work returned HTTP 200, Duration 19-24ms (fact-aab40d827262, fact-2da2e0d00672) | 追踪数据进一步证实业务流量正常，非全局应用挂起 |

**证据互证说明：**
Kubernetes 状态显示 Pod 因 Liveness Probe 返回 500 而崩溃 (证据 #4)，且退出码为 137 (证据 #2)。然而，Metrics 和 Tracing 数据以及日志均显示业务端口 (`/work`) 正常响应 200 (证据 #6, #7)。这表明应用主进程存活且响应业务流量，但探针指定的路径或依赖存在故障。由于 Metrics 缺乏内存使用趋势数据，退出码 137 是源于内存溢出 (受限于 96Mi 的 Limit) 还是应用内部因探针失败导致的资源回收或外部中断，目前证据链存在冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 端点返回 500 或容器因资源限制异常终止 (未确认) → 
Kubelet 检测探针失败或容器进程退出 (Exit Code 137) → 
容器被强制重启并进入 BackOff 逻辑 → 
Pod 处于 CrashLoopBackOff 状态 (fact-b0505a2ca4ba, fact-e9addf0a8e45)
```

### 根因结论

**证据不足。**

当前事实存在逻辑冲突：
1.  **现象**：Pod 处于 `CrashLoopBackOff`，退出码为 `137` (fact-638ce0bb7931)，且 Liveness Probe 返回 `500` (fact-b0505a2ca4ba)。
2.  **矛盾**：业务流量 (`/work`) 显示 HTTP 200 且响应正常 (fact-49d577d387f6, fact-aab40d827262)。

无法确定根因，因为：
- **Exit Code 137 的成因未确认**：虽然内存限制为 96Mi (fact-002755fe8ab1) 使得 OOM Kill 成为可能，但 Prometheus 指标 (fact-56b7dc1b4c64) 仅记录了终止原因标记为 "Error" 且无样本计数趋势，未直接捕获到 `OOMKilled` 的显式证据。137 也可能是由其他 SIGKILL 引起。
- **Probe 失败的原因未确认**：应用主进程看似存活 (响应 /work 200)，但 Liveness Probe 失败的具体业务原因（是 `/health` 端点代码逻辑错误、依赖不可用，还是因 OOM 导致探针线程被杀）缺失决定性证据。

缺少包含 OOMKilled 明确标识的 Metrics 指标，或针对 Liveness 探针端点的独立错误日志/Trace 数据，以区分是内存资源瓶颈还是应用内部逻辑缺陷。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 24.4s
├─ 并发证据采集: 107.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 107.5s (Evidence 92.1s, RCA 15.2s)
└─ 汇总总结: 16.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
