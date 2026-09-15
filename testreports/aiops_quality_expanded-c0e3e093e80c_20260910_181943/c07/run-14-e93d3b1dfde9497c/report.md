## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff，容器 app 反复以 exit code 78 退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s `container.last_exit_code` | `container=app, exit_code=78` | 确认应用进程异常终止的具体退出码。 |
| 2 | K8s Event | K8s `event.message` | `Warning BackOff restarting failed container app...` | 证明 Kubelet 正在按指数退避策略反复重启该容器。 |
| 3 | Logging | ES `log.message` (pattern) | `CONFIG_MISSING`, `http_status=500`, path=`/work`, service=`aiops-lab-workload` | 直接表明应用逻辑中检测到了关键配置项缺失。 |
| 4 | Tracing | Tempo `application_span` | trace_id: `c6ffc9838e9b589ff9c084aa2ea07c2f`, `http.response.status_code=500`, `aiops.observed_mode=config_missing_exit` | 日志中的 trace_id 与 Span 完全匹配，证实该配置缺失发生在 HTTP 请求处理阶段并直接导致了 500 响应。 |
| 5 | Metric | Prometheus `kube_pod_container_status_waiting_reason` | `reason="CrashLoopBackOff", value=1` | 从 Prometheus 视角验证了当前的等待状态与 K8s 事件一致。 |

上述证据形成了完整的闭环：K8s 状态（#1, #2）记录了进程异常退出及重启循环；日志（#3）给出了明确的退出原因 `CONFIG_MISSING`；追踪数据（#4）通过关联的 trace_id 确认了该错误发生在服务请求处理链路中，而非纯粹的启动阶段；指标数据（#5）进一步佐证了当前的故障状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用关键配置缺失 (ConfigMap/Env) → 启动/请求逻辑抛出 CONFIG_MISSING 错误并退出 (Exit Code 78) → Kubelet 频繁重启容器失败 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：应用容器 `app` 在启动或处理请求时检测到关键配置项缺失，导致进程以退出码 78 终止，进而引发 K8s 的 CrashLoopBackOff。

**支撑证据：**
1.  **日志直接证据**：Elasticsearch 日志多次聚合出 `pattern: {"event": "http_request", "level": "error", "message": "CONFIG_MISSING", ...}` 模式（证据 #3），明确指出了应用层的失败原因。
2.  **追踪印证**：Tempo 的 Trace Span 数据（证据 #4）中，`aiops.observed_mode` 字段值为 `config_missing_exit`，且 `http.response.status_code` 为 500。该 Span 的 `trace_id` 与日志中记录的 trace_id 一致，证明了配置缺失是在请求处理时触发的确切事实。
3.  **系统状态**：K8s 事件和指标均一致反映了 `CrashLoopBackOff` 状态（证据 #2, #5），排除了其他非配置类故障（如 OOMKill 或镜像拉取失败）的可能性。

**缺失事实：**
尽管根因已确认为“配置缺失”，但输入中 `unknowns` 明确指出缺失的具体配置项名称（Key）及对应的 ConfigMap/Secret 完整内容不可知，且无法获取崩溃前最后一次容器进程的底层日志以定位具体代码行号。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 18.2s
├─ 并发证据采集: 97.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 97.3s (Evidence 87.4s, RCA 9.7s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
