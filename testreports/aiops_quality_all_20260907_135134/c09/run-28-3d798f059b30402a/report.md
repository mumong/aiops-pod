## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 状态为 NotReady，Readiness Probe 持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (fact-987ab652d4c4) | 提供探针故障的早期证据：应用端口尚未建立连接。 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-d2d4cd54d646) | 证实应用进程已启动并监听，但健康检查持续被拒绝。 |
| 3 | Logging | Elasticsearch | 模式 `dependency unavailable` (HTTP 503, path `/work`, service `aiops-lab-workload`) 出现 8 次；`allocated_mib` 在观测窗口内保持为 `0` (fact-1db7f1a90735 等)。 | 确认 503 故障的根源逻辑是“依赖不可用”，并提示启动时内存分配为 0 的异常状态。 |
| 4 | Tracing | DeepFlow (L7 Flow) | 9 条等价的 `GET /work` 流量返回 `response_code: 503`，源 `172.16.104.55` 指向目标 `172.16.104.35` (fact-325edf851687 等)。 | 从网络流量维度独立确认业务接口持续返回 503。 |

**证据印证说明：**
Kubernetes 探针从 `connection refused` 演变为 `HTTP 503`，证明应用容器已启动（与重启次数 `0` 及 K8s State `phase=Running` 一致）。Logging 中的 `dependency unavailable` 模式解释了 `503` 的具体业务含义，并伴随内存分配值为 `0` 的记录，与探针的判定逻辑形成闭环。DeepFlow 流量数据在跨网段（源 IP 差异）场景下均复现了该 503 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖不可用（或初始化阶段内存分配异常） → 应用进程启动并监听端口，但服务逻辑立即返回 503 → Kubelet Readiness Probe 探测 /ready 接口收到 503 响应 → Pod Ready 状态转为 False，对外呈现 NotReady 症状
```

### 根因结论

已确认根因为：应用启动时因内部依赖不可用（伴随 `allocated_mib: 0` 的异常现象），导致服务在就绪状态下持续返回 HTTP 503，致使 Kubernetes Readiness Probe 判定失败。

证据支撑：
- 探针记录：连续收到 `503` 状态码（事实 #2）。
- 日志记录：应用进程明确上报 `dependency unavailable` 错误（事实 #3）。
- 流量记录：网络侧确认 `GET /work` 请求持续被拒绝（事实 #4）。

尚未明确的事实：
- 具体是哪一个底层依赖组件（如数据库、中间件）不可用。
- `allocated_mib: 0` 的具体成因（是资源限制配置错误还是内存初始化失败）导致了依赖加载失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 27.8s
├─ 并发证据采集: 51.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 51.3s (Evidence 40.0s, RCA 11.1s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
