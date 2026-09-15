## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | container.last_terminated_reason: Error | 指示容器非正常终止 |
| 2 | K8s State | Pod | container.last_exit_code: 78 | 确认进程退出码，非OOMKilled(137) |
| 3 | K8s Event | Pod | Back-off restarting failed container app | 描述 CrashLoopBackOff 现象 |
| 4 | Logging | Elasticsearch | http_request error: CONFIG_MISSING, status=500, path=/work (8次) | 证实应用启动/运行失败的具体错误为配置缺失 |
| 5 | Tracing | Deepflow/Tempo | L7 Flow: GET /work -> 500, trace_id e.g. 35171f43b5d98aebd6019469374b813c | 网络层确认请求被应用处理并返回错误，定位错误在应用侧 |

- K8s 状态（exit code 78、CrashLoopBackOff）与日志、Trace 深度结合，证实失败原因并非资源限制（如 OOM）或网络不通，而是应用逻辑报错。
- 日志明确出现 `CONFIG_MISSING` 模式且伴随 HTTP 500 响应，直接解释了 exit code 78 的来源。
- 缺乏对 ConfigMap `workload-code` 内部内容的直接校验事实，仅能确认应用侧报告了配置缺失，无法确认是 ConfigMap 未挂载还是内容不完整。

## 🎯 根因分析 · g1

### 因果链

```text
配置项缺失 (应用层) → 进程以异常码 78 退出 → Kubelet 触发重启循环 (CrashLoopBackOff) → Pod Ready=False，服务不可用
```

### 根因结论

- **已确认的根因**：应用启动或运行过程中检测到关键配置缺失（`CONFIG_MISSING`），导致进程以 exit code 78 异常退出，进而引发 Kubernetes 的 CrashLoopBackOff 状态。这一结论由 Pod 退出码事实 (fact-32fa11b1eeb3) 及 Elasticsearch 中的 `CONFIG_MISSING` 错误日志 (fact-0a029b3fc3e0 等) 互为印证。
- **证据不足说明**：现有证据仅证明了“应用认为配置缺失”，但未提供 ConfigMap `workload-code` 的实际内容校验数据。因此，无法区分是 ConfigMap 本身未定义/未挂载，还是 ConfigMap 中存在定义但缺少了应用所需的特定 key，或是路径映射错误。需要补充 ConfigMap 资源定义与挂载配置的对比事实以完成闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 46.6s
├─ 并发证据采集: 55.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 55.8s (Evidence 47.6s, RCA 8.0s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
