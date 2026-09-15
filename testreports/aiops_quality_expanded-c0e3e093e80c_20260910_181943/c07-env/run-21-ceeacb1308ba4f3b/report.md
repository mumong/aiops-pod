## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload 定义中缺少必要的 'APP_REQUIRED_CONFIG' 环境变量，导致容器启动时执行命令检测到该变量为空，从而主动调用 sys.exit(78) 退出进程，引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff (container=app) | 确认 Pod 处于持续崩溃重启循环状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error | 确认容器因错误退出，而非正常停止 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 78 | 提供进程退出的确切退出码，指向应用层主动报错 |
| 4 | K8s Event | kubernetes | `event.message`: Back-off restarting failed container app (over 44m, x188) | 描述故障持续时间与重启频率，排除瞬时抖动 |
| 5 | Logging | elasticsearch | `log.message`: "APP_REQUIRED_CONFIG environment variable is missing" | 直接记录启动时缺失环境变量的日志信息 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1, reason=CrashLoopBackOff | 独立验证容器处于等待重启状态的指标状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 13, container=app | 量化确认容器已重启 13 次 |

**证据说明：**
Kubernetes 事实确认了 Pod `app` 容器处于 `CrashLoopBackOff` 状态并因 Error 退出，且退出码为 78。Metric 数据独立印证了这一状态。Elasticsearch 日志提供了关键缺失信息：缺少 `APP_REQUIRED_CONFIG` 环境变量。退出码 78 结合该日志内容，高度指向应用检测到配置缺失后主动终止。由于 Tracing 数据为空，故障链断点在进程内部执行逻辑，未观测到上游依赖或流量异常。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中缺失 'APP_REQUIRED_CONFIG' 环境变量 → 容器启动检查发现变量为空 → 调用 sys.exit(78) 主动终止进程 → 触发 CrashLoopBackOff 重启循环
```

### 根因结论

已确认的根因为：**Pod 定义中缺少必要的环境变量 `APP_REQUIRED_CONFIG`**。

该根因直接导致了 `workload` 容器的启动失败。诊断证据支持如下：
1. **直接证据**：Elasticsearch 日志（#5）明确指出启动时检测到的错误是 "APP_REQUIRED_CONFIG environment variable is missing"。
2. **行为印证**：容器退出码为 78（#3），结合缺失变量的日志，符合应用在发现关键配置缺失时主动调用 `sys.exit()` 终止进程的行为模式（而非因 OOM 或信号导致的异常退出）。
3. **状态确认**：Kubernetes 状态（#1, #2）和 Prometheus 指标（#6, #7）一致证实了容器因该退出行为陷入了持续的崩溃重启循环。

现有证据链完整，足以解释当前 `CrashLoopBackOff` 的故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-v10/workload: 43.0s (Evidence 36.9s, RCA 6.1s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
