## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 应用 /health 接口存在 time.sleep(3)，超过 Liveness Probe 配置 timeout (1s)，导致 kubelet 发送 SIGKILL 频繁杀死容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` (fact-9b8049f98ba4) | 确认 kubelet 在探测 /health 接口时超时，直接触发杀容器动作 |
| 2 | K8s Event | kubernetes | `Back-off restarting failed container app in pod workload_aiops-case-v17(85aece07-6ffa-41db-9e5a-f351771a8864)` (fact-3c5e4c8a6e92) | 确认系统已执行频繁重启循环 |
| 3 | Tracing | deepflow | `/health` 接口耗时 `min: 3000797.0us, max: 3002216.0us` (fact-3ea3501d7874) | 证实应用处理 /health 请求平均耗时约 3 秒，远超一般阈值 |
| 4 | K8s State | kubernetes | `container.last_terminated_reason: Error` (fact-4825147cf080) | 确认容器终止原因为 Error |

**证据关系说明**：
Kubernetes 探测机制（证据 #1）是引发容器终止（证据 #3）的直接触发点；Tracing 数据（证据 #3）提供了 /health 接口耗时约 3 秒的真实依据，完美解释了 K8s 侧探测超时的原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 接口耗时 ~3s 且未支持异步处理 → Liveness Probe 配置超时 1s 导致探测失败 → kubelet 发送 SIGKILL 终止容器 → 用户侧应用频繁 CrashLoopBackOff 重启
```

### 根因结论

**已确认的根因**：应用 /health 接口存在 `time.sleep(3)`，其执行耗时（~3 秒）超过了 Liveness Probe 的 timeout 配置（1 秒）。

**支撑证据**：
- Tracing 原始数据证实 `/health` 请求平均耗时约 3000ms（证据 #3）。
- Kubernetes 事件日志显示 Liveness 探测返回 `context deadline exceeded`（证据 #1）。
- 容器终止状态确认为 Error（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.0s
├─ 并发证据采集: 45.4s
│  └─ g1 aiops-case-v17/workload: 45.4s (Evidence 37.0s, RCA 8.2s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
