## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | RecentRestart | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，重启 6 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 触发机制：健康检查失败的具体错误 |
| 2 | K8s State | Kubelet | `Exit Code: 137` | 机制确认：容器被强制终止的信号 |
| 3 | K8s Event | Kubelet | `Killing container app failed liveness probe, will be restarted` | 过程确认：kubelet 执行终止动作 |
| 4 | K8s State | Kubelet | `Waiting Reason: CrashLoopBackOff` | 现象：系统当前的容器状态 |
| 5 | Logging | ES (Trace ID: 25eab16af3118069854cfa67f4691f08) | `http_request` completed at `21:01:35.480Z` (Status: 200) | 冲突证据：应用本身在重启前仍处理请求并返回 200 |
| 6 | Tracing | Tempo | Span `25eab16af3118069854cfa67f4691f08` 标注 `observed_mode: liveness_fail` | 关联证据：200 响应与探针失败状态共存于同一 Trace 上下文 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason = 1 (reason=Error)` | 状态印证：确认上一次终止原因为非 0 退出 |

证据矛盾：应用侧日志显示 5 分钟前成功返回 HTTP 200（Fact #5），且 Tracing 确认了该正常请求与探针失败的共存（Fact #6），但 Kubelet 侧却记录了 HTTP 500 探针失败（Fact #1）。这表明探针检测到的 500 异常可能与正常业务流量（200）不同，或者应用内部状态在两次请求间发生了瞬态切换，导致探针超时或报错而业务流量正常。日志未捕获导致 500 的堆栈。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部异常/超时（仅触发探针，业务流量正常） → 探针返回 HTTP 500 → Kubelet 终止容器（Exit 137） → CrashLoopBackOff
```

### 根因结论

**已确认的根因**：健康检查探针失败触发了容器的强制重启机制。

- **机制确认**：Pod 中的 `app` 容器因 Liveness Probe 返回 HTTP 500 而被 kubelet 强制杀死（Exit Code 137），导致状态进入 `CrashLoopBackOff`（Fact #1, #2, #3）。
- **现象特征**：日志和追踪数据表明，虽然探针在 21:02:14 触发失败，但在此前的 21:01:35，应用成功处理了 HTTP GET 请求并返回 200（Fact #5, #6）。这种“业务正常、探针失败”的矛盾现象通常指向探针配置过于敏感（如超时阈值过低）或应用在处理探针请求时发生了特定的异常（如依赖缺失、连接池耗尽等未命中主业务流的路径）。

**缺失的决定性事实**：
由于日志中未能捕获到探针失败瞬间的应用堆栈（`unknowns` 列表），且缺乏探针配置参数（如 timeoutSeconds, failureThreshold），无法进一步诊断应用侧返回 500 的**具体代码级根因**（如空指针、上游依赖超时或特定的异常处理逻辑）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 57.9s
├─ 并发证据采集: 79.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 79.5s (Evidence 70.5s, RCA 8.9s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime, pod-oomkilled
