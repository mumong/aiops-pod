## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod NotReady (Readiness probe failed) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` Ready=False, ContainersNotReady; 重启次数 0 (fact-24ca6d3f9245) | 确立 Pod 持续处于 NotReady 状态且未发生重启，排除因 OOMKilled 或 CrashLoop 导致的启动失败 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (持续 113m, 累计 2287 次) (fact-a9d1f7e0824b) | 定义核心故障现象：应用服务启动成功但健康检查持续报 503 错误 |
| 3 | Logging | Elasticsearch | `dependency unavailable` (http_status: 503, path: `/work`); trace_id: `4838cbefda0b49701d86d8d6ea4bf034` (fact-7bdfc02f7388) | 锁定应用层故障点：应用在处理 `/work` 请求时因内部依赖不可用返回 503 |
| 4 | Tracing | Tempo | Flow `GET /work` → 503, trace_id: `6f6bdf0cfdfd482b9d037f0ef4321493` (fact-114ca8885591) | 从链路层面证实应用自身代码逻辑（或依赖调用）导致 503 响应 |
| 5 | Tracing | Deepflow | HTTP GET `/work` dst_ip: `172.16.104.35` (Pod IP) → 503, 9 次聚合记录 (fact-021519f42c11) | 确认 503 响应来自 Pod 内部（目标 IP 与 Pod IP 一致），非网络中断或路由问题 |

**证据总结**：
Pod 处于 Running 状态但未 Ready。Kubelet 探针持续记录到 HTTP 503 错误。日志（fact-3）和链路追踪（fact-4）在相同的 `GET /work` 路径上互相印证，明确显示应用进程存活但因内部依赖不可用（"dependency unavailable"）而返回 503。Deepflow 流量记录（fact-5）进一步证实该 503 响应由 Pod 自身产生，排除了网络策略阻断的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖服务不可用 → 应用处理 /work 请求返回 HTTP 503 → Kubelet 就绪探针连续 2287 次失败 → Pod 状态变为 NotReady (ContainersNotReady)
```

### 根因结论

已确认的根因为：**应用进程因内部依赖不可用而持续返回 HTTP 503，导致 Kubelet 就绪探针（Readiness Probe）持续失败**。

证据（fact-a9d1f7e0824b, fact-7bdfc02f7388, fact-114ca8885591）一致表明应用容器已成功启动（重启次数为 0），但应用逻辑中调用的内部依赖组件或资源处于不可用状态，致使应用自身无法提供正常服务响应。探针（针对 /work 端点）捕捉到的 503 错误直接反映了这一应用层故障。

**待确认**：具体是哪个内部依赖服务（如数据库、缓存或下游微服务）返回了不可用状态，以及是否存在网络策略（NetworkPolicy）或 Sidecar 配置问题阻碍了该依赖连接。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 21.1s
├─ 并发证据采集: 567.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 567.5s (Evidence 559.1s, RCA 8.2s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
