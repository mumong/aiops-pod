## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器状态：`CrashLoopBackOff`；最后终止原因：`Error`；最后退出码：`2`；重启次数：`13` | 明确应用进程反复异常终止的直接表现 |
| 2 | K8s Event | kubernetes | `Warning BackOff: Back-off restarting failed container app` (32s x203 over 45m) | 确认 Pod 处于持续崩溃重启循环中，kubelet 正在退避 |
| 3 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: Error | 独立确认上次容器终止原因为 Error，非 OOM 或配置错误 |
| 4 | Metric | prometheus | `container_memory_working_set_bytes` 范围 `1.56MiB - 17.15MiB`，当前 `1.8MiB` | 内存使用极低，排除资源超限（Limit 96Mi）引发的 Kill |
| 5 | Logging | elasticsearch | `error` 级别日志：`"runtime process exiting"` (HTTP status: 500)，持续于 `18:54:15` - `19:15:08` | 确认应用内部错误导致进程主动退出，非底层系统崩溃 |
| 6 | Tracing | tempo | Trace `1946b848...`：`GET /work` 返回 `HTTP 500`，应用观测模式 `runtime_exit` | 精准定位崩溃触发路径为 `/work` 端点请求处理失败 |

**证据互证说明：**
Kubernetes 状态（#1）确认进程异常终止，Metric 内存数据（#4）排除了资源压力，Logging（#5）和 Tracing（#6）共同将原因锁定在业务层：即 `/work` 端点处理请求时产生 500 错误并导致 runtime 进程主动退出，从而引发 K8s 的 CrashLoopBackOff 循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码缺陷 → GET /work 端点处理请求返回 500 错误 → 触发 runtime process exiting (exit code 2) → 容器崩溃并触发 CrashLoopBackOff
```

### 根因结论

**已确认根因：**
工作负载 `aiops-case-06/workload-7679bcf76-n5vp8` 中的 `app` 容器存在应用层代码缺陷。具体表现为处理 `GET /work` 请求时发生异常（日志显示 `runtime process exiting`），导致进程以退出码 2 终止。Kubernetes 检测到进程退出后执行重启，因重启过于频繁触发了 `BackOff` 机制（证据编号 1, 2, 5, 6）。内存资源使用情况正常（证据编号 4），排除了资源限制导致的 OOM Kill。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 21.9s
├─ 并发证据采集: 92.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 92.7s (Evidence 82.2s, RCA 10.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
