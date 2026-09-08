## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用进程在启动后执行启动校验时因检测到必要配置缺失（CONFIG_MISSING）主动调用 sys.exit(78) 终止运行。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `exit_code: 78`, `waiting_reason: CrashLoopBackOff` | 证实应用进程非崩溃退出，而是主动调用退出码 78 终止，引发重启循环。 |
| 2 | K8s Event | kubernetes | `Warning BackOff 2m5s (x313 over 71m) kubelet Back-off restarting failed container app` | 提供重启频率和时间跨度（71分钟313次），确认为持续的启动校验失败循环。 |
| 3 | K8s Event | kubernetes | `message: cni.projectcalico.org/podIP: 172.16.104.15/32` | 确认 Pod 网络已分配且正常，排除因 CNI 网络不可达导致的启动失败。 |
| 4 | Logging | elasticsearch | `http_request` `ERROR` `CONFIG_MISSING` `http_status: 500` `path: /work` `occurrence_count: 8` | 直接展示应用内部错误日志，明确失败原因为“配置缺失”，定位到校验失败的具体点。 |
| 5 | Tracing | tempo | `GET /work` `status_code: 500` `attributes: { "aiops.observed_mode": "config_missing_exit" }` `trace_id: 65684c8c074b2b13bde640e742613caa` | 与日志事实 `fact-6940352077a6` 共享 Trace ID，跨维度证实请求在应用层因配置检查被拒绝，未发生底层运行时故障。 |

**证据关系说明：**
1.  **K8s 状态 (Fact 1)** 提供的 `exit_code: 78` 是判定“正常退出”的关键证据，它解释了为何 Kubernetes 报 `Error` 而非 `OOMKilled` 或 `OOMKilled` 类错误。
2.  **日志 (Fact 4)** 与 **Tracing (Fact 5)** 互相印证：Trace ID `65684c8c074b2b13bde640e742613caa` 连接了 `http.request` 日志与应用 Span，两者均指向 `/work` 接口因 `CONFIG_MISSING` 返回 500 错误，直接解释了应用为何执行 `sys.exit(78)`。
3.  **K8s 事件 (Fact 2)** 提供了宏观现象，即这种“配置缺失 -> 退出 -> 重启”的循环已经持续了 71 分钟。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动配置校验失败 (CONFIG_MISSING) → 应用主动执行 sys.exit(78) 终止 → 容器退出码非 0 触发 K8s 重启策略 → CrashLoopBackOff 导致 Pod 不断重启
```

### 根因结论

已确认的根因是**应用进程在启动阶段的配置校验逻辑检测到了缺失的必选配置（触发 `CONFIG_MISSING` 事件），导致程序主动调用 `sys.exit(78)` 退出**。

*   **现象支撑**：K8s 容器状态显示退出码为 `78`（Fact 1），且 Kubernetes Event 记录了大量 BackOff 重启事件（Fact 2）。
*   **应用层根因**：Elasticsearch 日志聚合显示在 `/work` 路径反复出现 `CONFIG_MISSING` 错误（Fact 4），Tracing 数据也通过 `aiops.observed_mode: config_missing_exit` 属性证实了这一路径上的拒绝行为（Fact 5）。
*   **已知未知**：现有事实未指明 `workload-code` ConfigMap 中具体缺失的键名（如特定的 Key 或环境变量），因此根因定位在应用层的校验逻辑触发，而非具体的缺失参数名称。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 24.5s
├─ 并发证据采集: 100.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 100.2s (Evidence 91.9s, RCA 8.1s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
