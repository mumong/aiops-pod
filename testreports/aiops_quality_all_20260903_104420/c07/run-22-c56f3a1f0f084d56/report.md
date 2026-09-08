## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器 app 重启 11 次，退出码 78。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-dff5cbc6b-kmfxx` 状态 `Running`，容器 `app` 退出码 78，重启 11 次，处于 CrashLoopBackOff | 描述异常现象与当前状态 |
| 2 | K8s Event | Kubernetes | `Warning BackOff 2m51s (x156 over 37m)` 重启失败容器 app | 佐证异常持续存在且频率增加 |
| 3 | K8s Event | Kubernetes | `Ready=False`，消息 `containers with unready status: [app]` | 确认应用未就绪，阻断服务 |
| 4 | Logging | Elasticsearch | 模式 `CONFIG_MISSING`，HTTP 500，路径 `/work` (8 次，时间窗口 14:10:55 ~ 14:31:43) | 指向应用层配置缺失的具体报错模式 |
| 5 | Tracing | Tempo | Span `GET /work`，`http.response.status_code=500`，属性 `aiops.observed_mode=config_missing_exit` | 关联日志 trace_id 并确认代码执行路径 |
| 6 | Tracing | Deepflow | L7 Flow `GET /work -> 500`，9 次等效流量，时间窗口 22:10:53 ~ 22:31:41 | 从网络侧独立观测同样的异常请求模式 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1 (CrashLoopBackOff)`，`kube_pod_container_status_restarts_total=11` | 从监控侧确认异常状态和重启次数 |

**证据关联说明：**
Kubernetes 状态（#1）与 Metric（#7）在现象层相互印证，确认了 Pod 的异常重启循环。应用层根因由 Logging（#4）、Tracing（#5）、Deepflow（#6）共同锁定在 `GET /work` 路径的 `CONFIG_MISSING` 错误，其中 Tempo Span 和 Deepflow Flow 的 `trace_id` 或请求模式与日志聚合的时间窗重合，表明该错误是直接导致容器退出的触发器。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 server.py 启动/处理请求时检测到 CONFIG_MISSING → 进程以非零退出码 78 终止 → Kubernetes 持续重启失败 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用配置缺失**（证据 #4, #5, #6）。

应用容器 `app` 在启动或处理 `/work` 请求时，因检测到关键配置缺失（日志报 `CONFIG_MISSING`，应用观察模式为 `config_missing_exit`），主动以退出码 78 终止。Kubernetes 依据重启策略反复拉起容器，导致 Pod 陷入 CrashLoopBackOff 循环。

**局限/未确认事实：**
日志与应用仅报告了 `CONFIG_MISSING`，未指明具体的配置文件或环境变量 Key 名称。输入中提及的 ConfigMap `workload-code` 缺失了哪些具体 Key，或是否存在注入/挂载错误，目前**证据不足**，无法进一步判定是代码硬编码要求与 ConfigMap 内容不匹配，还是 K8s 注入配置失败。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 25.5s
├─ 并发证据采集: 80.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 80.9s (Evidence 68.7s, RCA 12.0s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
