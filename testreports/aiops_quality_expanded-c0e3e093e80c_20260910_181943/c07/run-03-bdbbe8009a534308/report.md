## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，容器反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: reason=Error | 确认容器异常退出，直接触发崩溃机制 |
| 2 | K8s Event | kubernetes | `event.message`: Warning BackOff restarting failed container app | 确认 Kubelet 正在因失败而退避重启 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: exit_code=78 | 确认进程以非系统标准退出码终止 |
| 4 | K8s Config | kubernetes | `container.resource_request/memory`: 24Mi; `container.resource_limit/memory`: 96Mi | 资源限制配置，排除 OOM 内存耗尽迹象 |
| 5 | Logging | elasticsearch | `log.message`: pattern=CONFIG_MISSING, http_status=500, path=/work (8次重复) | 明确日志报错模式为配置缺失，关联请求失败 |
| 6 | Tracing | deepflow | `l7_flow`: HTTP GET /work, response_code=500 (9次) | 验证外部 HTTP 请求直接返回 500 错误 |
| 7 | Tracing | deepflow | `trace_ids` (如 a358165e4c5df7b2882c057473693f30): 与日志聚合记录 ID 高度一致 | 将 HTTP 流量与具体错误日志关联，确认业务层因果 |
| 8 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: reason=CrashLoopBackOff (value=1) | 从指标侧独立确认 Pod 处于崩溃循环状态 |

证据 5 (CONFIG_MISSING 日志) 与 6, 7 (HTTP 500 与 Trace 关联) 互相印证，说明应用进程在处理请求时主动报错退出；证据 1, 2, 8 确认了这种退出行为被 K8s 调度层接收并表现为 CrashLoopBackOff。资源信息 (4) 排除了内存超限导致的 OOMKill 可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码缺少关键配置 (CONFIG_MISSING) → 应用进程处理请求失败并以退出码 78 终止 → Kubelet 检测到容器非正常退出并触发重启 → Pod 进入 CrashLoopBackOff 状态，容器在 Running/Error 间反复切换
```

### 根因结论

已确认根因为**应用代码缺少必要配置**。
证据表明：应用容器在启动或处理请求期间因配置缺失 (`CONFIG_MISSING`) 而异常退出（Exit Code 78），并伴随 HTTP 500 错误响应（证据 5, 6, 7）。这种异常退出导致 Kubelet 触发重启机制，但因配置未修复，Pod 陷入 `CrashLoopBackOff` 状态（证据 1, 2, 8）。
缺失的具体配置文件名或环境变量键名未在当前事实中提供。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 24.9s
├─ 并发证据采集: 78.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 78.4s (Evidence 69.3s, RCA 9.0s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
