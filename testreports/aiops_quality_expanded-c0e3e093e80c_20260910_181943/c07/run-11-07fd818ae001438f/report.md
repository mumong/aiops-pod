## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod配置挂载错误或配置内容缺失导致应用启动失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod workload-dff5cbc6b-sjvxl 状态 `ContainersNotReady`，容器 `app` 状态 `CrashLoopBackOff`，重启次数 `8` | 确认应用处于持续崩溃重启的故障现象 |
| 2 | K8s State | kubernetes | 容器 `app` 上一次退出原因 `Error`，退出码 `78` | 确认应用非正常退出，提供排查方向 |
| 3 | Logging | elasticsearch | 错误日志模式：`event: http_request`, `level: error`, `message: CONFIG_MISSING`, `http_status: 500`, `path: /work`，8次出现 | 直接指出应用内部发生配置缺失错误 |
| 4 | Tracing | Tempo / Deepflow | 关联日志的 Trace ID `03bb71894f37a2749d62f867432270a1` 等，HTTP GET `/work` 返回 `500`，应用模式标记为 `config_missing_exit` | 从流量侧独立确认请求因配置问题导致 500 并触发退出 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (CrashLoopBackOff=1), `kube_pod_container_status_restarts_total` 持续增加 (5→8) | 指标持续同步 K8s 状态，确认故障处于持续活跃期 |

**证据链说明：**
日志中明确记录 `CONFIG_MISSING` 导致 HTTP 500，且应用退出码为 78，这解释了 K8s 记录的 `CrashLoopBackOff` 现象。Tracing 数据中的 `config_missing_exit` 标记及关联的 Trace ID 将日志与流量行为进行了闭环印证，确认故障发生在业务逻辑层而非 K8s 调度层。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动或运行所需的配置文件/内容缺失 (CONFIG_MISSING) → 业务处理逻辑抛出异常 (Exit Code 78) → 容器异常终止触发 K8s 重启策略 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为 **应用期望的配置文件或配置内容缺失**。
该根因由以下事实支撑：
1. **直接错误证据**：日志中 8 次出现 `message: CONFIG_MISSING` 且伴随 `http_status: 500`（证据 #3）；
2. **退出行为佐证**：容器退出码 `78` 明确指示因配置问题导致的终止（证据 #2）；
3. **全栈一致性**：K8s 状态 `CrashLoopBackOff`、Prometheus 重启计数增加（证据 #1, #5）均与“应用因配置错误反复重启”的模型完全吻合，且 Tracing 数据独立验证了请求失败的原因（证据 #4）。

现有的 Kubernetes 状态与指标仅展示了故障现象（Symptom），日志与追踪中的 `CONFIG_MISSING` 提供了决定性的业务根因证据，结论可发布。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 50.8s
├─ 并发证据采集: 67.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 67.6s (Evidence 58.7s, RCA 8.7s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
