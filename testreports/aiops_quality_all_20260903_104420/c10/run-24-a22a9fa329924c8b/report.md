## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | {'message': 'k8s.v1.cni.cncf.io/network-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_exit_code=137` | 容器进程被强杀，暗示 OOMKilled 或 SIGKILL |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 探针判定应用不健康，触发重启 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes`: max `15.6MB`，limit `96Mi` | 内存远低于限制，不支持 OOMKilled 直接推断 |
| 4 | Logging | Elasticsearch | Pattern: `http_status: 200` (8 occurrences) | 常规请求返回正常，与应用行为不一致 |
| 5 | Tracing | Tempo | `response.status_code=200`, `observed_mode=liveness_fail` | 探针视角与业务视角的响应状态存在冲突 |

**证据关系说明：**
- **冲突点**：退出码 137 (证据 1) 与 Metrics 的极低内存使用量 (证据 3) 形成矛盾，既不支持 OOMKilled，也缺乏其他 SIGKILL 的直接证据（如系统日志）。
- **探针异常**：Liveness 探针报告 HTTP 500 (证据 2)，但应用日志 (证据 4) 和业务 Span (证据 5) 均显示 HTTP 200。由于 `observed_mode=liveness_fail` 且未捕获到探针特有的报错 Flow，无法确定探针失败是应用逻辑异常、网络超时还是探针配置问题。
- **现状**：Pod 处于 CrashLoopBackOff 状态 (k8s event)，由于缺乏 Previous Logs 和探针失败的独立观测链路，根因无法闭合。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程被强制终止 (Exit Code 137) → 探针判定不健康 (Liveness 500) → 直接失败：Pod CrashLoopBackOff → 用户可见：应用重启/不可用
```

### 根因结论

**证据不足**。

虽然观察到容器反复崩溃（Exit Code 137）且 Liveness 探针失败（HTTP 500），但关键证据存在矛盾：
1. 内存指标（15.6MB）远低于硬限制（96Mi），排除了常见的 OOMKilled 场景。
2. 业务日志显示正常 HTTP 200，无法解释 Liveness 探针为何返回 500。

缺少以下决定性事实：
- 上一次崩溃前的应用日志（`previous_logs`），以查看是否存在未返回响应的异常或 panic。
- 探针失败时的完整链路日志或更细粒度的探针诊断信息，以区分是“应用返回 500”还是“探针超时/连接被拒”。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 27.9s
├─ 并发证据采集: 120.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 120.3s (Evidence 109.8s, RCA 10.1s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime
