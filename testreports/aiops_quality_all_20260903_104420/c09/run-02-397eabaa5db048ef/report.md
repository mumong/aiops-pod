## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | App handler at /work returns HTTP 503 due to 'dependency unavailable', causing readiness probe failures and NotReady status. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | Ready=False, Reason: ContainersNotReady | 直接确认 Pod 未就绪的状态 |
| 2 | K8s Event | Kubelet | Readiness probe failed: dial tcp 172.16.104.26:8080: connect: connection refused | 确认探测端口连接被拒绝 |
| 3 | K8s Event | Kubelet | Readiness probe failed: HTTP probe failed with statuscode: 503 | 确认应用返回 503 导致探测失败 |
| 4 | Logging | ES | pattern: `dependency unavailable`, http_status: 503, path: `/work` | 定位 503 的具体代码与逻辑原因 |
| 5 | Tracing | Tempo | GET /work, response_code: 503, span_id: `335ddbcc4b5024ee` | 链路追踪确认具体请求返回 503 |
| 6 | Tracing | Deepflow | Flow: GET /work -> 172.16.104.26:8080, response_code: 503 | 网络层流量确认 503 的来源与应用 |
| 7 | Metric | Prometheus | pod_phase: Running (1), restarts: 0 | 排除容器崩溃/频繁重启的可能性 |

**证据关系说明：**
- **K8s State (1)** 的状态由 **K8s Event (2, 3)** 解释，探针失败的根本原因是应用返回 **503**。
- **Logging (4)** 揭示了 503 的直接业务逻辑：`dependency unavailable`。
- **Tracing (5, 6)** 验证了该错误发生在 `/work` 路径，并与日志的模式、Pod IP 一致，排除了网络组件故障。
- **Metric (7)** 确认 Pod 处于 Running 且重启次数为 0，进一步锁定问题在应用逻辑层而非容器环境崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
依赖不可用 (dependency unavailable) → 应用返回 HTTP 503 → Readiness 探针接收 503 失败 → Pod 状态变更为 NotReady
```

### 根因结论

**已确认根因**：工作负载 `workload-5f4fb9ff45-cfzz6` 的内部依赖不可用，导致处理 `/work` 路径的请求时返回 HTTP 503，进而触发了 Readiness 探针失败与 Pod `NotReady` 状态。

**缺失决定因素**：虽然确认了依赖不可用的现象，但缺乏关于该依赖具体名称、类型（如环境变量、本地文件还是外部服务）以及其不可用原因的日志或配置证据。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 17.4s
├─ 并发证据采集: 93.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 93.9s (Evidence 83.9s, RCA 9.6s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
