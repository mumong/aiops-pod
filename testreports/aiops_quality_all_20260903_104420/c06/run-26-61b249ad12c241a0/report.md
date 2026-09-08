## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器 app 持续重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-06/workload-7679bcf76-w9s9c` 状态 `CrashLoopBackOff`，容器 `app` 重启 16 次，最后一次终止原因为 `Error`，退出码 2 | 确认 Pod 处于持续失败且正在尝试重启的异常状态 |
| 2 | K8s Event | Kubernetes | `Warning BackOff`：`back-off 5m0s restarting failed container=app`，事件持续 59 分钟内重复 246 次 | 证实重启动作频率极高且系统已触发退避机制 |
| 3 | Logging | Elasticsearch | 日志模式 `http_request`：`runtime process exiting`，`http_status: 500`，`path: /work`，时间范围 12:32 至 12:47 | 直接显示应用逻辑在处理 `/work` 时抛出 500 错误并导致进程退出 |
| 4 | Tracing | Deepflow | L7 Flow：GET `/work`，`response_code: 500`，重复 4 次，耗时 4616us 至 6226us | 从网络层视角独立印证了 `/work` 接口返回 500 错误的事实 |
| 5 | K8s Config | Kubernetes | 容器资源请求：`cpu: 20m, memory: 24Mi`；限制：`cpu: 200m, memory: 96Mi` | 提供资源基线，结合无 OOMKilled 状态，辅助排除硬内存限制导致的 Crash |

**证据交叉印证**：
K8s 状态（#1, #2）显示容器非正常退出并频繁重启；Logging（#3）与 Tracing（#4）从应用层和网络层共同指向同一个原因：对 `/work` 路径的请求导致应用内部 500 错误及进程终止。退出码 2 与日志中的 `runtime process exiting` 逻辑一致，进一步区别于 OOMKill (exit code 137)。

## 🎯 根因分析 · g1

### 因果链

```text
/work 端点代码逻辑错误（未捕获异常） → 返回 HTTP 500 Internal Server Error → 进程以非零退出码 2 强制终止 → 触发 Kubernetes CrashLoopBackOff 及周期性重启
```

### 根因结论

**已确认根因**：应用代码在处理 `/work` 端点时存在逻辑缺陷，导致运行时抛出未处理的内部错误（HTTP 500），进而引发进程异常退出（Exit Code 2）。

**证据支持**：
1.  **应用错误表现**：Elasticsearch 日志（证据 #3）在崩溃时间窗口内频繁记录 `http_status: 500` 伴随 `runtime process exiting`。
2.  **网络层验证**：Deepflow 追踪数据（证据 #4）聚合展示了针对同一资源 `/work` 的 4 次 500 响应。
3.  **容器状态关联**：Kubernetes 报告的状态为 `Error` 且退出码为 `2`（证据 #1, #2），符合业务逻辑崩溃特征，排除了基础设施层面的 OOMKill（通常为 137）或探针失败。

**已知局限**：
由于日志中 Trace ID 与当前日志批次不一致（未知项提及 `41ea4f...` 与 `5ece3a...` 不匹配），缺乏精确对应单次崩溃堆栈的详细 Trace 数据，且 Metrics 维度缺失，未能提供内存趋势佐证（尽管 Exit Code 2 已强烈暗示非 OOM）。当前证据链已足以定位根因为应用代码层面的 `/work` 端点处理错误。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.1s
├─ 并发证据采集: 96.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 96.7s (Evidence 86.6s, RCA 9.9s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled
