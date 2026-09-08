## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用启动配置缺失（CONFIG_MISSING）导致进程崩溃退出，触发 Kubelet 重启策略并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod `workload-dff5cbc6b-fkzvn` status: `Running`；container `app` restart_count: `8` (fact-1636937cb007) | 症状：容器已启动但频繁重启 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (fact-1822777947cd) | 机制：Kubelet 执行重启退避 |
| 3 | K8s Config | Kubernetes | container `app` resource limits: cpu=`200m`, memory=`96Mi` (fact-2b6c34a50354, fact-654dd5ce5a5e) | 上下文：资源配额正常，非资源限制导致OOM |
| 4 | Logging | Elasticsearch | pattern `CONFIG_MISSING` (http_status=500, path=/work)，累计 8 次 (fact-6423d1a8e1f4 等) | 根因：日志明确显示应用因配置缺失返回 500 |
| 5 | Tracing | Deepflow | L7 Flow GET `/work` response_code=`500`, 累计 9 次 (fact-80dca9b68ddb 等) | 根因：流量日志印证应用处理请求失败 |
| 6 | Tracing | Tempo | Span `GET /work` 状态码 500，attributes 显示 `aiops.observed_mode=config_missing_exit` (fact-0022d2f0ccba) | 根因：追踪数据确认应用因配置问题退出 |
| 7 | K8s State | Kubernetes | container `app` last terminated reason: `Error`, exit_code: `78` (fact-3fcea8c525f6, fact-de31fea5920d) | 根因：应用进程异常退出，退出码 78 对应配置错误 |
| 8 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` label `reason: Error` = 1 (fact-573b14114aae) | 验证：指标确认容器最后一次终止原因为 Error |

**证据印证说明：**
- **根因一致性**：日志 (fact-4) 报告的 `CONFIG_MISSING`、追踪 (fact-6) 中的 `config_missing_exit` 属性与退出码 78 (fact-7) 互相印证，共同指向应用启动/运行配置缺失。
- **状态一致性**：K8s Event (fact-2) 的 BackOff 警告与 K8s State (fact-1) 的重启计数、Metric (fact-8) 的终止原因标签，共同证实了应用崩溃后持续重试的 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动配置缺失 → 应用启动失败/进程退出(exit_code: 78) → Kubelet 频繁重启容器 → CrashLoopBackOff
```

### 根因结论

已确认根因：**应用启动配置缺失（CONFIG_MISSING）**。
该配置问题导致应用进程启动失败（日志 fact-4、追踪 fact-6 确认）并直接退出（退出码 78，事实 fact-7）。Kubernetes 容器运行时检测到退出后，依据重启策略不断尝试重启容器（重启次数 8 次，事实 fact-1），最终因频繁重启触发 Kubelet 的 BackOff 退避机制（事件 fact-2），表现为 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.1s
├─ 并发证据采集: 69.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 69.3s (Evidence 63.3s, RCA 5.9s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- 未调用 Runbook
