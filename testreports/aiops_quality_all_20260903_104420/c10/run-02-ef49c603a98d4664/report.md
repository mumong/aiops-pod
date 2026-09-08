## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | Pod workload-79d9f8fd88-sbqvc处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-6174d8e2a249) | 直接证明健康检查机制判定应用不健康 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (fact-16dedb57f9f2) | 确认 kubelet 正在执行重启逻辑，且已触发指数退避 |
| 3 | K8s State | Kubernetes | Container Exit Code: 137 (fact-74b51df89033) | 提供容器终止原因（被强制终止） |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值升至 15425536 bytes (~14.7MB)，接近 Limit 96Mi (fact-4f78e2899d68) | 记录异常发生前的资源占用情况 |
| 5 | K8s Config | Kubernetes | Resource Limit Memory: 96Mi (fact-cce011a0f17d) | 定义容器内存硬限制，为分析 OOM 或探针行为提供边界上下文 |
| 6 | Logging | Elasticsearch | `request completed` HTTP 200 `/work` 正常 (fact-015eecf81aaa) | 证明应用工作负载接口本身可用，非应用全局宕机 |
| 7 | Tracing | Deepflow | L7 Flow `GET /work` HTTP 200 (fact-100fffe34371) | 交叉验证工作接口功能正常 |

**证据综合分析**：
- **探针与状态**：Kubernetes 事件明确指出 Liveness 探针因 HTTP 500 失败，直接导致了 `Exit Code: 137`（SIGKILL）的容器终止（证据 #1, #3, #2）。
- **资源分析**：虽然内存使用量（证据 #4）曾接近 96Mi 的限制（证据 #5），但 K8s 事件 #1 提供了比 OOM 更直接的终止理由（探针失败）。此外，137 退出码通常关联 OOMKilled，但探针 500 错误是 kubelet 发起 `kill` 的前提。结合未检测到 OOMKilled 相关事件，当前证据链指向“探针失败”为主导机制，资源状态作为背景上下文。
- **应用可用性**：日志和链路追踪（证据 #6, #7）证实应用工作接口 `/work` 响应正常，排除了应用完全不可用的可能，进一步缩小了故障范围至 `/health` 端点特定的内部逻辑或依赖。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部逻辑/依赖异常(导致/health返回500) → Liveness探针连续失败 → kubelet判定不健康并发送SIGKILL → Pod进入CrashLoopBackOff状态
```

### 根因结论

**已确认根因**：Pod `workload-79d9f8fd88-sbqvc` 进入 CrashLoopBackOff 状态的根本原因是 **Liveness 探针失败**。
- 依据事实 #1，`kubelet` 记录到 Liveness 探针 `HTTP probe failed with statuscode: 500`。
- 依据事实 #3，容器以 `Exit Code: 137` (SIGKILL) 退出，这是 kubelet 在探针连续失败后终止容器的直接行为结果。
- 依据事实 #2，容器因反复崩溃进入 BackOff 重启循环。

**排除与未确认**：
- **排除 OOMKilled 为主因**：虽然内存使用量接近 Limit（事实 #4, #5），但 Kubernetes 事件明确记录了探针失败，且未提供 `OOMKilled` 事件作为直接终止原因，因此探针失败是触发当前循环的直接和决定性因素。
- **未确认因素**：应用内部导致 `/health` 端点返回 HTTP 500 的具体代码逻辑或内部依赖故障原因（如数据库连接超时、特定状态机错误等）在当前事实集中未包含应用内部堆栈或详细错误日志，因此属于 `unknowns`。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 35.9s
├─ 并发证据采集: 149.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 149.6s (Evidence 139.6s, RCA 9.9s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-notready-probe-failed
