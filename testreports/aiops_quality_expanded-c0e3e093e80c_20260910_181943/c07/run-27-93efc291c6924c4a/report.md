## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，app 容器反复以 Exit Code 78 崩溃退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Container app` 处于 `CrashLoopBackOff`，最后终止原因为 `Error`，退出码为 78，重启次数 14 次 | 确认应用进程因主动异常退出陷入重启循环 |
| 2 | K8s Event | Kubernetes | `Warning BackOff`: "Back-off restarting failed container app in pod workload-dff5cbc6b-sjvxl_aiops-case-07" | 记录 kubelet 因频繁崩溃而背压暂停重启的集群侧状态 |
| 3 | Logging | Elasticsearch | 8 条 `CONFIG_MISSING` 错误日志，均发生在请求 `/work` 时，返回 HTTP 500，`allocated_mib` 均为 0 | 直接暴露应用因配置缺失而进入故障处理模式 |
| 4 | Tracing | Deepflow/Tempo | Flow 与 Span 关联 trace_id `64132b2c9d9b8077c1ac955acb517247`；属性 `aiops.observed_mode: "config_missing_exit"`，响应码 500 | 证实应用进程内部已明确识别到配置缺失状态并终止处理 |

上述证据形成闭环：Kubernetes 侧捕获到进程频繁以 78 码退出；日志层显示应用在接收到 `/work` 请求时打印 `CONFIG_MISSING` 并返回 500；追踪层通过关联的 trace_id 证实该 500 响应源于应用内部 `config_missing_exit` 模式。多维数据一致指向应用层因配置问题主动崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失（未指定有效的 FAILURE_MODE 或关键配置项） → server.py 进入 config_missing_exit 模式处理请求 → 应用主动返回 HTTP 500 并退出（Exit Code 78） → kubelet 触发 CrashLoopBackOff 重启
```

### 根因结论

**已确认根因：应用因配置缺失主动退出引发重启循环。**
现有证据确凿：应用日志明确记录 `CONFIG_MISSING` 错误（#3），追踪数据证实请求处理因 `config_missing_exit` 模式失败（#4），集群侧 K8s 状态与日志时间线吻合，证实应用进程主动终止（#1）。根本原因在于 `server.py` 无法加载到有效的 `FAILURE_MODE` 配置，导致其按预设的安全机制主动退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 14.1s
├─ 并发证据采集: 89.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 89.8s (Evidence 78.6s, RCA 11.0s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
