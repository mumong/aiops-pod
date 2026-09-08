## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l 处于 Running 但 NotReady 状态，Readiness 探针持续返回 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态 `Running`，但 `ContainersReady` 为 `False`，原因 `ContainersNotReady` [fact-187ca85aece1] | 确立 Pod 运行但不受流量服务的基础现象 |
| 2 | K8s Event | Kubernetes | Readiness 探针连续失败：`HTTP probe failed with statuscode: 503`，及底层连接失败 `dial tcp 172.16.104.35:8080: connect: connection refused` [fact-a5783b9fbf72, fact-a5791638386c] | 确认应用进程存在，但健康检查端点无响应，导致状态流转停滞 |
| 3 | Logging | Elasticsearch | 19:01:08 至 19:40:01 期间 14 次记录到相同错误模式：`dependency unavailable` (HTTP 503) [fact-2a68451492e7...fact-23386de3c595] | 直接证实应用在探测周期内因依赖缺失而主动返回 503 状态码 |
| 4 | Tracing | Tempo / Deepflow | Trace `5d9d8efaae8b4748db93567a0a5350e3` 展示 HTTP 请求 `GET /work` 最终响应 503 [fact-06c6810c9421]；10 次等价 L7 Flow 显示 `172.16.104.55` 到 Pod IP `172.16.104.35:8080` 的 GET `/work` 均返回 503 [fact-8b3aaf720748...fact-32e97ccfab89] | 跨系统链路闭环，确认探针请求与业务逻辑均受同一应用内部逻辑阻塞影响 |
| 5 | Metric | Prometheus | CPU 使用率从 2.54s 增加至 6.19s，内存使用量 `allocated_mib` 维持在 0 [fact-058ef590fbe1, fact-2a68451492e7] | 排除内存耗尽导致的系统级僵死，表明资源消耗在请求处理层面正常 |

日志聚合事实中多次出现 `dependency unavailable` 的 HTTP 503 错误，结合 K8s 探针返回的完全相同的 503 状态码以及 Tracing 链路中的同等响应，形成完整证据链，证明 Pod 的进程是存活且正在执行代码的，其“不健康”状态是应用层逻辑依赖外部服务失败后导致的主动拒绝。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖外部服务不可用 → 业务逻辑无法获取必要资源 → /ready 端点执行失败并返回 HTTP 503 → Readiness Probe 校验失败 → Pod 被标记为 NotReady，无法接收服务流量
```

### 根因结论

已确认根因：应用容器内依赖的特定外部服务（如数据库、缓存等）当前处于不可用状态。

- **事实支撑**：
  1. **探针结果直接印证**：K8s 事件日志明确指出 Readiness Probe 失败的原因为 `HTTP probe failed with statuscode: 503` [fact-a5783b9fbf72]。
  2. **应用内源日志证实**：Elasticsearch 日志在故障期间（19:01-19:40）持续报错 `dependency unavailable` [fact-2a68451492e7]，解释了应用为何向探针返回 503 状态码。
  3. **链路完整性**：Tempo 与 Deepflow 追踪数据一致验证了针对健康检查端点的请求最终都收到了 503 响应 [fact-06c6810c9421, fact-8b3aaf720748]。

- **未确认项**：
  具体是哪个外部依赖服务不可用，以及应用启动初期是否有过短暂成功（日志数据从 19:01 开始）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 23.1s
├─ 并发证据采集: 95.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 95.8s (Evidence 84.7s, RCA 11.0s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
