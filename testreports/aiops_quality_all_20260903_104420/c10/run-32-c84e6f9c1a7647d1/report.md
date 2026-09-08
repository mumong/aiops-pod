## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Container 'app' has a strict memory limit of 96Mi which is insufficient for the Python process, causing the kernel OOMKiller to send SIGKILL (exit code 137); application logs remain healthy until the abrupt termination. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` (fact-00ece17adfd8) | 确立异常根因：内存限制极低，不足支撑 Python 进程。 |
| 2 | K8s Event | Kubernetes | `Exit Code: 137` (fact-6699d89dd8fe), `Exit Code: 137` (fact-1d1d4a3a722f) | 确认系统级 OOMKiller 触发了 SIGKILL 终止进程。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error` (fact-64b295a56601, fact-7cd15c1872a6) | 证实容器因异常退出进入重启等待循环。 |
| 4 | K8s State | Kubernetes | `restart_count: 33`, pod `ContainersReady: False` (fact-2b5f91070cbe, fact-7d15ad27f878) | 证实应用频繁崩溃且集群判定应用处于未就绪状态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (Reason: CrashLoopBackOff), `kube_pod_container_status_last_terminated_reason = 1` (Reason: Error) (fact-4da452e1f39c, fact-8ba715003614) | 从监控维度印证容器处于 CrashLoopBackOff 状态且最后终止原因为 Error。 |
| 6 | Logging | Elasticsearch | `pattern: request completed, http_status: 200`, `numeric_fields.allocated_mib: 0 -> 0`, 记录数 8 (fact-09717ab98082 聚合) | 证实容器在被 OOMKiller 杀死前仍在健康处理请求，无应用层报错。 |
| 7 | Tracing | Tempo + Deepflow | `span: GET /work, http.response.status_code: 200` (fact-720b5f52748e), `l7_flow: response_code: 200` (fact-0f01327b8fc9 聚合) | 确认请求在超时或杀死的边缘仍成功返回 HTTP 200，限定异常发生在应用逻辑执行之后、资源耗尽的瞬间。 |

上述证据形成完整的因果链条：Kubernetes 监控与状态日志显示容器频繁崩溃重启（证据 3、4），Exit Code 137 证实由系统 OOMKiller 强杀（证据 2）。配置项显示该限制仅为 96Mi（证据 1），且底层监控确认了 Error 终止原因（证据 5）。日志与追踪数据表明，异常前应用均正常响应 200 请求且无应用日志报错（证据 6、7），进一步排除了业务逻辑故障，将根因锁定在硬性的极低内存上限上。

## 🎯 根因分析 · g1

### 因果链

```text
内存硬限制过低(96Mi) → Python进程触发内核OOMKiller → 容器进程被强杀(SIGKILL/退出码137) → CrashLoopBackOff
```

### 根因结论

已确认根因为：Pod `workload-79d9f8fd88-sbqvc` 中 `app` 容器被配置了极低且不足以支撑 Python 运行的内存硬限制（96Mi），导致内核 OOMKiller 频繁终止容器。

- **现象支撑**：容器持续触发 CrashLoopBackOff（fact-64b295a56601），重启次数达 33 次（fact-2b5f91070cbe）。
- **机制支撑**：容器退出码为 137，表明被系统信号强杀（fact-4feda419abfc）；Kubernetes Event 中记录 Exit Code 137（fact-6699d89dd8fe）。
- **配置支撑**：内存限制被固定为 96Mi（fact-00ece17adfd8）。
- **排除干扰**：应用日志（fact-09717ab98082）和 HTTP 追踪（fact-720b5f52748e）均在终止前显示 HTTP 200 正常响应，排除应用层报错导致的崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 21.2s
├─ 并发证据采集: 112.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 112.6s (Evidence 106.4s, RCA 6.0s)
└─ 汇总总结: 15.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
