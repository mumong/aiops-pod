## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，重启次数为 9 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-dff5cbc6b-kmfxx` 状态为 `Running`，但 `app` 容器处于 `CrashLoopBackOff` 状态；最后一次异常终止原因为 `Error`。 | 确立现象：应用进程已退出但容器仍在尝试重启，且非资源不足。 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app`，自 25 分钟内已发生 112 次。 | 确认重启行为已被 kubelet 捕获。 |
| 3 | K8s State | Kubernetes | `app` 容器的退出码 (`exit_code`) 为 **78**。 | 指向具体的程序异常退出逻辑（通常为配置/初始化错误）。 |
| 4 | Logging | Elasticsearch | 聚合日志模式 `CONFIG_MISSING`，`http_status: 500`，`path: /work`；连续记录中 `allocated_mib` 始终为 `0`。 | 提供直接因果：HTTP 请求触发配置缺失报错并主动终止。 |
| 5 | Tracing | Tempo | 链路 `9e99fbd922a97ca99308339b3fbad526` 对应 `GET /work`，返回 500；Span 属性显示 `aiops.observed_mode: config_missing_exit`。 | 交叉验证日志：Trace 确认了导致退出的具体操作模式为“配置缺失”。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 为 `Error`，重启总数 `9`。 | 独立观测源印证 K8s 状态及退出性质。 |

证据说明：
1.  **Kubernetes** 观察到容器以错误状态退出（exit 78）并进入 CrashLoopBackOff 循环，排除了 OOM 等常见系统级故障（因 `Error` 原因且资源 Request/Limit 较小）。
2.  **Logging** 和 **Tracing** 提供了明确的退出机制证据：日志中的 `CONFIG_MISSING` 模式与 Trace 中的 `config_missing_exit` 模式完全一致，且均关联到处理 `/work` 请求时。
3.  **Metric** 仅提供了重启次数的状态映射，与 K8s 状态互为印证。

## 🎯 根因分析 · g1

### 因果链

```text
代码中配置项缺失 (事实：日志 CONFIG_MISSING/Trace config_missing_exit) 
  → 请求处理逻辑触发退出 (事实：HTTP 500 / Work 路径异常) 
  → 进程以退出码 78 主动终止 (事实：Container exit_code: 78) 
  → kubelet 执行 Back-off 重启，Pod 进入 CrashLoopBackOff (事实：Event BackOff / Container Waiting Reason)
```

### 根因结论

**已确认的根因**：应用容器在启动并运行后，在处理 `GET /work` 请求时检测到**内部配置项缺失**（Code 逻辑触发 `config_missing_exit`）。该异常导致应用主动以退出码 **78** 终止进程，进而触发 Kubernetes 的重启策略，最终形成 CrashLoopBackOff 循环。

**证据编号**：
- 触发与机制：证据 #4 (Logging `CONFIG_MISSING`, `path: /work`)，证据 #5 (Tracing `config_missing_exit`, `GET /work`)。
- 终止与现象：证据 #3 (Exit code 78)，证据 #1 & #2 (K8s `CrashLoopBackOff`, `Error`, `BackOff Event`)。

**未确认事项**：
- 具体缺失的配置项 Key 名未在日志或 Trace 中暴露（证据 #4 仅显示通用 `CONFIG_MISSING` 模式）。
- 导致该配置缺失的根因（如部署配置变更、ConfigMap 版本错误或遗漏）需要进一步检查 Deployment 或 ConfigMap 变更历史才能确认。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 17.0s
├─ 并发证据采集: 112.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 112.8s (Evidence 101.4s, RCA 11.2s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
