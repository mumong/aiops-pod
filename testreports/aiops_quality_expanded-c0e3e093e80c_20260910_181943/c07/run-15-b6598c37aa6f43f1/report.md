## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod 容器退出码 78 (ERRCONFIG) 及日志 'CONFIG_MISSING' 表明应用启动失败，根本原因为容器运行时无法访问或解析所需的配置文件（通常指向挂载的 ConfigMap 'workload-code' 内容缺失或卷挂载路径配置错误）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态为 `CrashLoopBackOff`，`last_terminated_reason` 为 `Error`，退出码 78 | 确认核心故障现象，容器非正常终止 |
| 2 | K8s State | Kubernetes | Pod `ContainersReady` 与 `Ready` 状态均为 `False`，提示 `ContainersNotReady` | 确认应用未进入就绪状态，服务不可用 |
| 3 | Logging | Elasticsearch | 聚合日志模式：`http_request` 返回 `http_status: 500`，`message: CONFIG_MISSING`，路径 `/work` (20:33 - 20:57) | 应用内部报错表明配置缺失，触发直接退出 |
| 4 | Tracing | Tempo | 流量 `GET /work` 对应 `trace_id: c6ffc9838e9b589ff9c084aa2ea07c2f`，应用标记 `observed_mode: config_missing_exit` | 关联日志与流量，证实退出系由配置丢失导致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 10，`waiting_reason` 为 `CrashLoopBackOff` | 印证反复重启循环且系统处于等待重启状态 |

**证据分析**：
Kubernetes 状态确认了 Pod 持续退出（Exit Code 78）并进入 CrashLoopBackOff；日志 `CONFIG_MISSING` 与 Trace 中的 `config_missing_exit` 模式在相同 Trace 上下文中一致，直接定位到应用启动失败的原因为配置缺失；指标证实了重启循环的客观发生。

## 🎯 根因分析 · g1

### 因果链

```text
配置文件缺失或挂载异常 (未确认的具体环境原因) → 应用启动/请求时触发 CONFIG_MISSING (机制) → 进程以 Exit Code 78 终止 (直接失败) → Pod 进入 CrashLoopBackOff 状态 (现象)
```

### 根因结论

已确认根因为**应用因缺失必需配置而终止**。证据显示应用进程在启动或处理 `/work` 请求时报告 `CONFIG_MISSING` 错误（证据 #3, #4），随后以退出码 78 退出（证据 #1），导致 Kubernetes 持续重试并进入 CrashLoopBackOff（证据 #1, #5）。

具体为何缺失（例如 ConfigMap 挂载错误、内容丢失或路径配置错误）在输入事实中无直接证据（如卷挂载配置或 ConfigMap 状态），因此具体配置挂载问题标记为“未确认”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 18.4s
├─ 并发证据采集: 77.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 77.9s (Evidence 69.8s, RCA 8.0s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
