## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | 应用代码在处理 /work 请求时触发运行时崩溃导致进程退出（Exit Code 2） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-7679bcf76-jwr8b` 状态 `Running`，容器 `app` 退出码 `2`，终止原因 `Error`，重启次数 `25` | 确立应用进程已崩溃且被 K8s 重启的事实 |
| 2 | K8s Event | Kubernetes | `BackOff 2m50s` (x475 over 107m) `Back-off restarting failed container app in pod workload-7679bcf76-jwr8b...` | 证明崩溃持续发生且符合 `CrashLoopBackOff` 行为 |
| 3 | K8s Config | Kubernetes | 容器内存限制 `96Mi`，内存请求 `24Mi`；CPU 限制 `200m`，CPU 请求 `20m` | 提供资源边界上下文，但无证据指向资源超限 |
| 4 | Logging | Elasticsearch | `http_request` error 模式：`message: "runtime process exiting"`, `http_status: 500`, `path: "/work"`, `trace_ids: ["72d4f55afad60666f47a49161a6df3c9", "66f8517c6ab359b396ba34556ba3082f", "fb6fd50f7d4673a02b8767471e797abe", "1a2507787060edb94b3020127f39412a"]` | 定位异常发生在处理 `/work` 请求期间，直接伴随进程退出 |
| 5 | Tracing | Tempo | `GET /work` Span 详情：`aiops.observed_mode: "runtime_exit"`, `http.route: "/work"`, `http.response.status_code: 200`, `trace_id: "130bdd4836bc750bcf687e89b717aebe"` | 印证 `/work` 路径触发了运行时模式变更 (`runtime_exit`)，确认故障域 |

**证据关联说明：**
日志记录的 `runtime process exiting` 发生在 `/work` 请求期间（证据 #4），这与追踪数据中 `aiops.observed_mode` 显示为 `runtime_exit` 且路径为 `/work` 的 Span（证据 #5）完全一致。Kubernetes 侧记录的退出码 `2` 和终止原因 `Error`（证据 #1）由上述运行时错误直接引发，导致 Pod 进入持续崩溃重启循环（证据 #2）。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work 路径时触发运行时异常 → 内部崩溃机制 (observed_mode: runtime_exit) → 进程非零退出 (Exit Code 2) → Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认根因为：**应用代码在处理 `/work` 请求路径时触发运行时崩溃（Runtime Error），导致进程退出码 2 并重启。**

该结论由以下事实互相印证：
1. **Kubernetes 状态确认异常**：容器以非零退出码 `2` 终止（证据 #1），并触发了 K8s 默认的 `BackOff` 重启逻辑（证据 #2）。
2. **代码逻辑定位**：日志显示 `runtime process exiting` 且伴随 HTTP 请求 `/work`（证据 #4）。
3. **追踪链路闭合**：对应 `/work` 路径的 Trace Span 明确记录了 `aiops.observed_mode: "runtime_exit"`（证据 #5）。

**缺失的决定性事实**：虽然可确认是“运行时崩溃导致退出”，但缺乏具体导致崩溃的堆栈跟踪（Stack Trace）或详细错误文本（需通过代码审查获取），无法进一步定位具体的代码异常行或异常类型。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 19.9s
├─ 并发证据采集: 108.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 108.0s (Evidence 100.4s, RCA 7.4s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
