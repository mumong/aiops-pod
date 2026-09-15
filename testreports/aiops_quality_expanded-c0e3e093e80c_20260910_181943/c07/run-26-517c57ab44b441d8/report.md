## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | 应用容器启动后执行 /work 请求时因缺失必要配置项(CONFIG_MISSING)抛出内部500错误，该异常逻辑导致进程以退出码78主动终止，进而触发Kubernetes的CrashLoopBackOff重启机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 2m49s (x199 over 47m) kubelet Back-off restarting failed container app` | 确认容器启动后频繁被 kubelet 强制重启，持续 47 分钟以上 |
| 2 | K8s State | Kubernetes | `exit_code: 78` | 容器以特定非零退出码终止，表明应用层主动抛出故障退出 |
| 3 | Logging | Elasticsearch | `CONFIG_MISSING`, `http_status: 500`, `path: /work`, `service: aiops-lab-workload` (连续记录中 `allocated_mib` 均为 0) | 直接指向应用在处理 `/work` 请求时因缺少配置抛出 500 错误 |
| 4 | Tracing | Deepflow | `GET /work` HTTP 500, `src_ip: 172.16.104.8`, `dst_ip: 172.16.104.63` | 证实请求在应用侧即被拦截并返回 500，排除网络或路由故障 |
| 5 | Tracing | Tempo | `trace_id: 64132b2c9d9b8077c1ac955acb517247`, `attributes: aiops.observed_mode: config_missing_exit` | 与日志关联，确认应用内部观测到的故障模式为配置缺失导致的退出 |

**证据关联分析：**
日志与 Trace 高度一致：Trace 显示 `/work` 请求返回 500，日志记录同样的 `CONFIG_MISSING` 错误及 `http_status: 500`。退出码 `78` 与 Trace 中的 `config_missing_exit` 模式相符，直接导致 kubelet 检测到容器异常退出并持续执行 `BackOff` 重启策略。

## 🎯 根因分析 · g1

### 因果链

```text
应用期望的配置项在工作目录(/work)中缺失 → 应用处理请求时捕获配置缺失(CODE_MISSING)并主动以退出码 78 终止进程 → kubelet 检测到容器异常退出并触发 CrashLoopBackOff 重启机制 → Pod 状态显示为 CrashLoopBackOff
```

### 根因结论

已确认的根因是**应用因缺失必要配置项导致启动后立即终止**。

证据表明：应用在接收到 `/work` 请求时，因 `CONFIG_MISSING` 抛出 500 内部错误并主动以 `exit_code: 78` 终止进程。这一行为触发了 Kubernetes 的重启机制，导致 Pod 进入 `CrashLoopBackOff` 状态。

虽然根因明确，但细节证据不足：无法从现有事实中确认 ConfigMap `workload-code` 中具体缺失的是哪个配置键值，也无法确定退出码 `78` 在应用层代码中的确切语义定义。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.0s
├─ 并发证据采集: 55.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 55.6s (Evidence 45.8s, RCA 9.7s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
