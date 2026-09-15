## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl (aiops-case-07) stuck in CrashLoopBackOff with repeated exitCode 78 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.last_terminated_reason`: Error | 确认 Pod 处于持续重启故障状态 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 78; `container.restart_count`: 21 | 确认进程频繁异常退出 |
| 3 | K8s Event | Kubernetes | `event.message`: Warning BackOff 32s (x378 over 85m) kubelet Back-off restarting failed container app | 确认 kubelet 观察到 378 次重启并进入退避 |
| 4 | Logging | Elasticsearch | Pattern: `CONFIG_MISSING`, `http_status`: 500, `path`: `/work`, `service`: `aiops-lab-workload`; Occurrence: 8 | 确认应用层在退出前检测到配置缺失并返回错误 |
| 5 | Tracing | Deepflow | HTTP GET `/work`, `response_code`: 500, Occurrence: 9 | 确认流量侧观测到服务在重启前产生 500 错误 |
| 6 | Tracing | Tempo | `aiops.observed_mode`: `config_missing_exit`; `http.response.status_code`: 500 | 确认应用代码层记录的具体故障模式 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 20; `kube_pod_container_status_waiting_reason`: 1 | 辅助印证容器重启次数与等待状态 |

证据交叉验证：Kubernetes 状态表明 Pod 因退出码 78 进入 CrashLoopBackOff；日志（Fact 4）与追踪（Fact 6）均指向 `CONFIG_MISSING` 且伴随 HTTP 500 错误；追踪数据（Fact 5）进一步确认了该 500 错误在重启前发生。

## 🎯 根因分析 · g1

### 因果链

```text
配置缺失 (Fact 4/6) → 进程返回退出码 78 并记录 config_missing_exit (Fact 2/6) → Kubelet 检测到进程退出并触发 CrashLoopBackOff (Fact 1/3)
```

### 根因结论

已确认的根因是容器应用 `app` 因检测到配置缺失（`CONFIG_MISSING`）而异常退出（Exit Code 78）。

- **应用行为**：日志显示应用在启动或运行期间多次（8次）记录 `CONFIG_MISSING` 错误，并通过 HTTP 500 响应请求（Fact 4）；追踪记录显示应用明确以 `config_missing_exit` 模式退出（Fact 6）。
- **系统响应**：Kubernetes 检测到容器以错误状态终止（Exit Code 78），导致 Pod 处于 `CrashLoopBackOff` 状态并频繁重启（Fact 1, 2, 3）。

**未知领域**：现有事实无法查明该配置（如具体的 ConfigMap 或文件路径）为何缺失，也未查明应用代码中退出码 78 的具体语义定义。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 23.4s
├─ 并发证据采集: 62.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 62.7s (Evidence 53.3s, RCA 9.2s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
