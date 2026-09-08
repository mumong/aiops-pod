## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用依赖服务不可用导致 Readiness Probe 持续返回 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `ContainersReady=False`, 原因: `ContainersNotReady`, 消息: `containers with unready status: [app]` (`fact-102699d9db39`) | 确认应用容器未就绪，处于持续失败状态 |
| 2 | K8s State | Kubernetes | `Ready=False`, 原因: `ContainersNotReady`, 消息: `containers with unready status: [app]` (`fact-a01b475fac17`) | 确认 Pod 层面 Ready 状态为 False |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0`，`sample_count=1` (`fact-bd64d6079ac1`) | 排除因 OOM 或 CrashLoop 导致重启引起的 NotReady |
| 4 | Logging | Elasticsearch | 8 条模式化日志 `dependency unavailable`, `http_status=503`, `path=/work` (`fact-5f4448a4318b` 等) | 直接观测到应用业务层无法获取依赖，返回 HTTP 503 |
| 5 | Tracing | Deepflow | 9 次等价 L7 Flow: `GET /work`, 响应码 `503`, `src_ip=172.16.104.19` 到 `dst_ip=172.16.104.26` (`fact-5a0e422f0500` 等) | 从网络流量层面确认对 `/work` 端点的请求全部返回 503 |
| 6 | Tracing | Tempo | `GET /work` span 返回 `http.response.status_code=503`, `aiops.observed_mode=readiness_fail` (`fact-58193054b9df`) | 关联 Readiness 探针检查动作与 503 业务失败直接关联 |

**证据关联说明：**
- 状态层 (事实 1, 2) 显示 Pod 持续 NotReady 但重启次数为 0 (事实 3)，说明容器仍在运行。
- 日志层 (事实 4)、网络流量层 (事实 5) 和 Trace 层 (事实 6) 在相同的时间窗内一致指向 `/work` 路径返回 503，证明 Readiness Probe 失败的根本原因是业务依赖不可用。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用健康检查端点 GET /work 返回 503 → Readiness Probe 持续失败 → Pod 状态变更为 NotReady
```

### 根因结论

已确认根因为**应用依赖服务不可用**。
具体表现为：应用容器（`app`）运行中但无法访问依赖，导致健康检查端点 `/work` 持续返回 `503 Service Unavailable`（见事实 4、5、6）。由于 Readiness Probe 判定失败，Pod 无法被标记为 Ready，对外表现为服务不可用（见事实 1、2）。因应用未发生崩溃（`restart_count=0`，见事实 3），Pod 状态保持为 `Running` 但 `NotReady`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.1s
├─ 并发证据采集: 47.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 47.3s (Evidence 40.1s, RCA 7.0s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
