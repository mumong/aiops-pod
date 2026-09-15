## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | {'message': 'k8s.v1.cni.cncf.io/networks-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Running; `container.restart_count`: 0; `annotation cni.projectcalico.org/podIP`: 172.16.104.16/32 | 确认应用容器进程存活但未发生重启，排除应用本身崩溃，聚焦于就绪逻辑问题。 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused`; 后续发生多次 HTTP 503 | 明确应用未监听 8080 端口（连接被拒），且应用内部 `/ready` 逻辑最终报出 503。 |
| 3 | Tracing | Deepflow/Tempo | `HTTP GET /work` 返回 503; `TraceID`: 118cdbf67902f1230e2f38d3ff619e5b (关联 Temp/Deepflow) | 确认请求到达应用内部，但应用层明确返回 503 并伴随 `readiness_fail` 模式。 |
| 4 | Logging | Elasticsearch | `pattern: "dependency unavailable"`, `http_status: 503`, `path: /work`; 窗口内 8 次发生 | 揭示 503 的内部确切原因：应用自身报告底层依赖服务不可用。 |

证据间逻辑互证：K8s Event 中的“连接被拒”证实探针无法通过底层 TCP 建立连接；后续日志与 Trace 数据进一步表明，应用层 `/work` 路由能处理请求但主动返回 503，并声明“依赖不可用”。这表明故障核心在于应用运行时的依赖服务异常，导致探针最终失败。

## 🎯 根因分析 · g1

### 因果链

```text
未确认的具体依赖异常 → 应用返回 HTTP 503 dependency unavailable → K8s Readiness Probe 失败 → Pod 状态 NotReady
```

### 根因结论

**已确认部分**：应用 Pod 当前因健康检查持续失败（先报连接被拒，后报 HTTP 503）处于 `NotReady` 状态，未重启。

**证据不足**：虽然日志明确指出应用内部发生了“dependency unavailable”（依赖不可用），但缺乏关于具体哪个依赖服务不可用（如数据库、缓存或第三方 API）以及其不可用原因（宕机、配置错误、网络策略阻断）的确切事实。因此，具体的依赖级根因无法确定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 22.8s
├─ 并发证据采集: 70.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 70.5s (Evidence 61.5s, RCA 8.8s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
