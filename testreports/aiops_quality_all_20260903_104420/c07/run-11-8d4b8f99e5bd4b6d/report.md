## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 容器应用被配置为 config_missing_exit 故障模式，导致启动时因 CONFIG_MISSING 错误返回 HTTP 500 并直接退出（Exit Code 78），引发 Kubelet 反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `last_exit_code`: 78 | 确认应用进程因应用层错误强制退出 |
| 2 | K8s Event | kubernetes | `BackOff` 66 次 (over 18m): "Back-off restarting failed container app" | 确认可视重启震荡现象，非调度或网络故障 |
| 3 | Logging | elasticsearch | `pattern`: CONFIG_MISSING, `http_status`: 500, `path`: /work, `occurrence_count`: 8 | 直接证明应用因配置缺失主动返回 500 并退出 |
| 4 | Tracing | deepflow+tempo | `GET /work` (span_id: 31c3bc9e6fee046d, trace_id: da9999ae734835080b2f252e105e1ce7): `response_status_code`: 500, `aiops.observed_mode`: config_missing_exit | 追踪链路确认 HTTP 500 由应用内部配置缺失引起，属于预期行为而非后端错误 |

**证据印证说明**：
K8s 状态显示应用以 Exit Code 78 反复重启（#1, #2），日志详细记录了每次退出前均返回 HTTP 500 并报错 `CONFIG_MISSING`（#3）。Tracing 数据（#4）不仅复现了该 HTTP 500 响应，还通过 `aiops.observed_mode` 确认这是配置缺失导致的受控退出行为。证据之间形成完整闭环，排除底层基础设施故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 业务层主动返回 HTTP 500 → 进程以 Exit Code 78 退出 → CrashLoopBackOff 震荡重启
```

### 根因结论

已确认根因：**应用逻辑配置缺失（config_missing_exit 故障模式）**。

应用启动后未能获取到关键配置，在 `/work` 端点触发业务逻辑时主动返回 HTTP 500 错误，并随即以 Exit Code 78 终止进程。日志重复出现 `CONFIG_MISSING` 错误码（#3），Tracing 链路证实 500 响应为应用内部控制逻辑所致（#4）。Kubelet 检测到此非零退出码后执行退避策略，导致当前持续重启震荡状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 42.1s
├─ 并发证据采集: 76.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 76.5s (Evidence 69.8s, RCA 6.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime, pod-oomkilled
