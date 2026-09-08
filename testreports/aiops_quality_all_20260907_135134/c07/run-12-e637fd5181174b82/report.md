## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器 app 反复重启退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `CrashLoopBackOff` (Waiting), `Error` (Terminated), `restart_count: 9` | 确认 Pod 处于反复重启状态 |
| 2 | K8s State | Kubernetes | Container `app` `exit_code: 78` | 确认应用进程以特定错误码主动退出 |
| 3 | Logging | Elasticsearch | Pattern `CONFIG_MISSING` (HTTP 500, path `/work`), 累计 8 次 (14:36:33 - 14:57:29) | 揭示进程退出前的直接报错模式 |
| 4 | Tracing | Tempo | Span `GET /work`, status 500, attribute `aiops.observed_mode: config_missing_exit` (Trace ID: `b3559561ac9acd05071836e31ce2b090`) | 从应用视角验证退出原因是配置缺失 |
| 5 | K8s Event | Kubernetes | `Back-off restarting failed container app` (2m37s over 22m) | 确认 Kubelet 已观察到退出并触发退避策略 |

**证据互证说明：**
1. K8s 指标（#1, #2）提供的 `restart_count: 9` 与 `exit_code: 78` 确认了故障现象是应用进程异常终止。
2. 日志（#3）与 Tracing（#4）共同指向了具体的退出机制：应用在处理 `/work` 请求时检测到 `CONFIG_MISSING` 后主动抛出 500 错误并终止进程（`config_missing_exit`）。
3. K8s 事件（#5）记录了系统层面对上述异常的周期性重启响应，形成从“应用报错退出”到“系统重启失败”的完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用 server.py 逻辑中缺失关键配置项 → 请求处理期间触发 CONFIG_MISSING 异常 → 进程以 exitCode 78 异常退出 → Kubelet 检测到容器非正常退出并进入 CrashLoopBackOff
```

### 根因结论

已确认的根因是应用代码（`/opt/aiops/server.py`）在处理 `GET /work` 请求时，主动检测到关键配置缺失并抛出 `CONFIG_MISSING` 异常，进而以退出码 78 终止进程，导致 Kubelet 不断重启容器。

证据链如下：
- **故障现象**：容器 `app` 处于 `CrashLoopBackOff` 状态，重启已达 9 次（证据 #1, #2）。
- **直接原因**：应用进程在退出前记录了 `CONFIG_MISSING` 错误，并返回 HTTP 500（证据 #3）。
- **代码逻辑确认**：Tracing 数据明确显示该次调用结束于 `config_missing_exit` 模式（证据 #4）。

**未知因素**：
当前日志和 Tracing 信息未指明具体缺失的配置键名（仅报告 `CONFIG_MISSING`），也无法提供 `server.py` 中检查该配置的代码细节。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 18.9s
├─ 并发证据采集: 100.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 100.0s (Evidence 89.7s, RCA 10.2s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
