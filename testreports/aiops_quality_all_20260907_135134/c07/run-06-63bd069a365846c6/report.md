## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用容器启动依赖的 ConfigMap 'workload-code' 中缺失关键配置项或文件，导致应用进程检测到 CONFIG_MISSING 错误并退出（exitCode=78），引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff ... 51s (x42 over 10m) kubelet Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn_aiops-case-07` | 展示应用容器经历频繁重启，进入退避重启阶段，确认 CrashLoopBackOff 现象 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 78` | 记录容器最后一次非零退出码 78，表明进程存在明确的业务级逻辑退出，而非资源限制导致的 OOMKilled |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.waiting_message: back-off 5m0s restarting failed container=app pod=workload-dff5cbc6b-fkzvn_aiops-case-07(bffd1771-cb0a-4bea-96ed-0a46e5b3a923)` | 明确 K8s 状态机的当前阻断原因，指出 kubelet 正在等待退避时间窗口 |
| 4 | K8s State | Kubernetes | `pod.condition: ContainersReady=False, reason=ContainersNotReady, message=containers with unready status: [app]` | 确认 Pod 处于运行中 (Running) 但应用容器不可用 (unready) 的状态 |
| 5 | K8s Event | Kubernetes | `event.message: Reason: CrashLoopBackOff`, `Annotations: cni.projectcalico.org/podIP: 172.16.104.7/32` | 补充 Pod 网络配置正常，无 CNI 相关报错，故障隔离在应用层 |
| 6 | K8s Config | Kubernetes | `container.resource_request.cpu: 20m`, `container.resource_limit.cpu: 200m`, `container.resource_request.memory: 24Mi`, `container.resource_limit.memory: 96Mi` | 展示资源请求与限制配置，证明配置中无异常极值，资源限制并非本次直接导致退出码 78 的原因 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 6` (sample_count: 28, min: 2.0, last: 6.0) | 提供重启次数的历史趋势证据，确认重启行为是累积且持续的 |
| 8 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (reason=CrashLoopBackOff), `kube_pod_container_status_last_terminated_reason: 1` (reason=Error) | 从监控视角印证 K8s 事件中的等待原因和最后一次终止原因，与 K8s 状态事实形成交叉验证 |
| 9 | Logging | Elasticsearch | `log.message: CONFIG_MISSING` (http_status: 500, path: /work, service: aiops-lab-workload), `occurrence_count: 8`, `trace_ids: [c42fa631d225def3cc3870919028d186, b3559561ac9acd05071836e31ce2b090, ...]` | 日志明确报错 `CONFIG_MISSING`，直接指向应用启动或运行时的关键配置缺失问题 |
| 10 | Tracing | Deepflow | `l7_flow: GET /work -> 500` (response_status: 3, dst_ip: 172.16.104.7, `trace_ids` 包含 `b3559561ac9acd05071836e31ce2b090`) | 网络流数据证实服务端点 `/work` 持续返回 500 错误，确认故障可被外部访问复现 |
| 11 | Tracing | Tempo | `application_span: GET /work, status_code: 500, attributes: aiops.observed_mode: config_missing_exit`, `trace_id: b3559561ac9acd05071836e31ce2b090` | 链路追踪确认 500 状态码源于应用内部的配置缺失逻辑（config_missing_exit），且日志中的 trace_id `b3559561...` 与 Tracing 完全关联，构建完整的调用链证据 |

**证据印证说明**：
K8s 事件与状态数据（#1, #2, #3, #4）确立了 `CrashLoopBackOff` 和退出码 78 的现象。日志（#9）提供了直接的应用层错误信息 `CONFIG_MISSING`，并通过 `trace_id` 与 Tracing 数据（#10, #11）关联，将底层的退出行为与上层的 HTTP 500 错误及具体的 `config_missing_exit` 诊断模式对应起来，排除了资源不足或网络不通等其他因素。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的 ConfigMap 'workload-code' 中缺失关键配置项 → 应用进程启动/初始化时检测到 CONFIG_MISSING 错误 → 进程以 exitCode=78 退出 → Pod 进入 CrashLoopBackOff 状态并反复重启
```

### 根因结论

已确认的根因是：**应用容器启动依赖的 ConfigMap 'workload-code' 中缺失关键配置项或文件**。
该配置缺失导致应用进程在启动或处理请求时检测到 `CONFIG_MISSING` 错误，从而以退出码 78 主动退出进程，Kubernetes 随后触发 CrashLoopBackOff 机制。证据编号 2（退出码 78）、9（日志 `CONFIG_MISSING`）和 11（Tracing 模式 `config_missing_exit`）互相印证了这一因果链。
未确认的事实包括 ConfigMap 的具体缺失键名或文件路径。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.4s
├─ 并发证据采集: 66.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 66.7s (Evidence 56.0s, RCA 10.6s)
└─ 汇总总结: 19.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
