## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | CrashLoopBackOff (restarts=16, exitCode=78) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason=Error`, `container.waiting_reason=CrashLoopBackOff`, `container.last_exit_code=78` | 确定应用进程以非零退出码 78 异常终止并触发 K8s 重启机制 |
| 2 | K8s Event | Kubernetes | `event.message: Warning BackOff ... Back-off restarting failed container app` | 确认 Kubelet 因频繁重启进入退避等待状态 |
| 3 | K8s Event | Kubernetes | `pod.condition: ContainersReady=False, Ready=False (reason: ContainersNotReady)` | 确认当前容器处于不可用状态 |
| 4 | Logging | Elasticsearch | `pattern: CONFIG_MISSING, http_status: 500, service: aiops-lab-workload` (occurrence_count: 8, 时间窗口: 2026-09-07T15:07:53Z 至 2026-09-07T15:34:05Z) | 暴露进程退出前的根本原因：应用逻辑报错配置缺失 |
| 5 | Tracing | Tempo | `span.attributes: aiops.observed_mode=config_missing_exit, http.response.status_code=500` | 追踪数据印证日志中的模式，确认错误发生在服务内部处理逻辑 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=16` (sample_count: 1) | 量化指标佐证了持续且高频的 CrashLoop 现象 |

**证据交叉印证：**
Kubernetes 状态与 Metric 指标客观证实了 `CrashLoopBackOff` 的现象（Restart=16, Exit=78）。日志维度提供了决定性线索 `CONFIG_MISSING`，Tracing 数据从链路层面确认了该错误是服务端主动抛出的 500 异常并附带特定的 `config_missing_exit` 模式。这三者结合，清晰指向非外部故障（如资源不足或网络不通）导致的程序级退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置变量缺失 → server.py 捕获缺失并记录 CONFIG_MISSING 错误 → 进程以退出码 78 (EX_UNAVAILABLE) 退出 → Kubelet 触发 CrashLoopBackOff (重启16次)
```

### 根因结论

已确认根因为：应用代码逻辑错误导致服务启动或运行失败。

- **证据引用**：
  1. 退出码 `78` 对应 Unix `EX_UNAVAILABLE`，通常表示服务不可用或配置缺失，与日志模式吻合（证据 #1）。
  2. 日志中高频出现的 `CONFIG_MISSING` 错误日志直接指向了应用层缺少关键配置（证据 #4）。
  3. 追踪数据确认了 500 错误是由服务端逻辑 `config_missing_exit` 触发的（证据 #5）。

- **缺失信息**：
  当前事实仅能定位到“配置变量缺失”这一抽象原因，无法确定缺失变量的具体 Key 名称，也无法确认是 ConfigMap 挂载错误还是环境变量漏配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.7s
├─ 并发证据采集: 82.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 82.5s (Evidence 72.2s, RCA 10.1s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
