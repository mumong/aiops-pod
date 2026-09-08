## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | workload-dff5cbc6b-fkzvn (aiops-case-07) CrashLoopBackOff, restart count 12 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | 容器退出码 78 | 确认容器进程以特定代码终止 |
| 2 | K8s State | K8s State | K8s Event: Back-off restarting failed container app (BackOff) | 确认 K8s 重启行为与指数退避 |
| 3 | K8s State | K8s State | Pod Phase: Running, 容器状态: CrashLoopBackOff | 确认 Pod 存活但应用未就绪 |
| 4 | Logging | Logging | log.message: `CONFIG_MISSING` (出现 8 次, 首次 `2026-09-07T14:46:54.437Z` 至末次 `2026-09-07T15:13:16.321Z`) | 应用层报错直接指向缺失配置 |
| 5 | Tracing | Tracing | HTTP Flow: `GET /work` -> 500 (8 次, 对应 8 个 trace_id) | 应用逻辑失败的具体请求模式与日志时间一致 |
| 6 | K8s Event | K8s Event | Reason: CrashLoopBackOff (153 次) | 确认重启失败状态持久化 |

证据印证与冲突：
- K8s 退出码 78 (证据#1) 与 Logging 的 `CONFIG_MISSING` (证据#4) 时间窗口完全重合，直接指向应用启动/运行时逻辑错误。
- Tracing 确认所有失败流量均针对 `/work` 路由且报 500 错误 (证据#5)，排除了集群网络或 K8s 基础组件层面的故障。

## 🎯 根因分析 · g1

### 因果链

```text
运行时环境缺少必要的配置数据（未确认缺失的 ConfigMap 具体 Key） → 应用 server.py 启动逻辑抛出 CONFIG_MISSING 异常 → 进程以退出码 78 终止，Kubelet 检测到异常退出并触发重启（指数退避） → Pod 陷入 CrashLoopBackOff，持续重启失败
```

### 根因结论

**已确认的根因：应用运行时报 `CONFIG_MISSING` 错误并以此退出码（78）终止。**
应用 `server.py` 在执行（或启动检查）时检测到关键配置缺失，主动抛错退出。Kubernetes 监控到进程异常退出后，触发重启策略。由于错误配置持续存在，Pod 不断重启并退避，最终表现为 `CrashLoopBackOff`。

**未确认事项：**
具体缺失的配置项名称或对应的 ConfigMap/Secret 键值（由 `unknowns` 字段及日志内容限定）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.5s
├─ 并发证据采集: 69.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 69.6s (Evidence 61.2s, RCA 8.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
