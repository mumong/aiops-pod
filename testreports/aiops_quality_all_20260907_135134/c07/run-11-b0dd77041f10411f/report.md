## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod 'workload-dff5cbc6b-fkzvn' (container 'app')处于CrashLoopBackOff状态，持续重启导致服务不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `exit_code`: 78 | 确认进程非正常终止，且返回特定代码 78。 |
| 2 | K8s Event | Kubernetes | `BackOff`: Back-off restarting failed container app (x8 over 20m) | 确认 Kubelet 因容器持续失败而进入指数退避重启。 |
| 3 | Logging | Elasticsearch | 8 次记录 `CONFIG_MISSING` 错误，`http_status`: 500，`path`: `/work` (窗口内 `allocated_mib` 持续为 0) | 证实启动时因缺少配置导致应用主动报错并终止。 |
| 4 | Tracing | Tempo / Deepflow | 9 次 HTTP 请求 `GET /work` 返回 500，`aiops.observed_mode`: config_missing_exit (Trace ID 重叠如 `a201a2c69fff6623eaef1c7d7b720c95`) | 提供链路视角证据，确认 500 错误与配置缺失直接相关。 |

**证据印证：**
1. K8s 状态的终止原因（Exit 78）与日志记录的 `CONFIG_MISSING` 模式及追踪标记 `config_missing_exit` 高度一致。
2. 日志显示 `allocated_mib` 始终为 0，解释了容器为何在启动初期即退出，且未触发 OOM（排除资源限制因素）。
3. 多个独立维度（Event、Logs、Tracing）均指向同一时间点范围内的同一故障模式，形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 → 启动时检查失败并记录 CONFIG_MISSING 日志 → 应用主动以 exit code 78 终止进程 → Kubelet 发现容器退出，重启后再次失败，进入 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用因检测到必要配置缺失（CONFIG_MISSING）而启动失败。**

应用代码在启动过程中检测到关键配置缺失，主动记录 `CONFIG_MISSING` 错误（Evidences 3, 4）并以退出码 78 终止进程（Evidence 1）。Kubelet 在检测到容器异常退出后，尝试重启但再次遇到相同问题，导致容器状态在 20 分钟内重启 8 次并进入 `CrashLoopBackOff`（Evidence 2）。

**缺失的决定性事实：**
现有证据仅能确认“配置缺失导致启动失败”，但未明确具体是哪个环境变量或配置文件缺失。若需进一步排查，需查看应用启动初期的详细配置加载日志或容器环境变量定义。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 24.4s
├─ 并发证据采集: 89.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 89.4s (Evidence 76.9s, RCA 12.3s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
