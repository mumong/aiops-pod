## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Container 'app' process crashes with exit code 2 upon execution of 'python3 /opt/aiops/server.py'. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason=Error; exit_code=2 | 确认容器进程以错误码 2 异常退出 |
| 2 | K8s Event | Kubernetes | BackOff  2m12s (x270 over 62m) restarting failed container | 证实 Pod 处于持续崩溃循环中 |
| 3 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason=1 (label: reason=Error) | 独立确认终端异常原因为 Error |
| 4 | Metric | Prometheus | kube_pod_container_status_restarts_total=16 | 量化崩溃循环的持续程度 |
| 5 | Logging | Elasticsearch | runtime process exiting (http_status=500) | 记录应用层进程退出的日志证据 |
| 6 | Tracing | Deepflow | GET /work response_code=500, duration=4623us | 关联一次导致异常退出的 HTTP 请求 |
| 7 | K8s Config | Kubernetes | container.resource_limit.memory=96Mi; cpu=200m | 确认资源硬限制配置（非 OOMKilled 特征） |

**证据分析**：
1-3 项在 Kubernetes 层和 Prometheus 层形成了闭环印证，一致指向容器进程因非零退出码（2）导致的 Error 状态，而非由调度器驱逐的 OOM 或系统错误。
5-6 项建立了应用行为与异常状态的关联：Deepflow 中的 500 错误 Flow 与 Elasticsearch 中 "runtime process exiting" 模式在时间上紧密相关，表明业务逻辑执行失败直接导致了进程崩溃。
7 项排除了内存硬限制导致的 OOMKilled 场景，辅助锁定为应用层面的运行时崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用执行 python3 /opt/aiops/server.py 异常 → 触发容器进程退出码 2 → kubelet 触发 BackOff 重启策略 → 状态 CrashLoopBackOff，应用无法访问
```

### 根因结论

异常组的根因已确认：容器内的应用进程 `app` 在尝试执行 `python3 /opt/aiops/server.py` 时发生崩溃。

这一根因由以下多维事实支撑：
*   **退出特征**：K8s 报告退出码为 2 (`fact-32a8e391cff1`, `fact-c57061a9d394`)，对应典型的参数错误或运行时逻辑异常。
*   **集群状态**：Pod 经历 16 次重启并进入 CrashLoopBackOff 状态 (`fact-9ef352bf6922`, `fact-dfd511b30b3e`, `fact-ec325a4f3738`)。
*   **应用行为**：日志记录到 "runtime process exiting"，且伴随 HTTP 500 响应 (`fact-1b5987cca1f8`, `fact-016bd4e3e2e9`)，表明崩溃发生在处理请求时。
*   **环境排除**：资源配置限制（96Mi/200m）不足以引起 OOM，排除了资源硬限制导致的外部终止 (`fact-d3fcf4e6c9d0`, `fact-81d93095c71c`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.6s
├─ 并发证据采集: 59.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 59.6s (Evidence 51.6s, RCA 7.8s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
