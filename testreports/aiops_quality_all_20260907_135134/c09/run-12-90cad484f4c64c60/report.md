## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod内的应用服务依赖的外部资源不可用，导致应用返回HTTP 503错误，Readiness Probe探测持续失败，使Pod状态维持NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (fact-06bd9c217ed9) | 明确探测目标及直接失败原因：连接被拒 |
| 2 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-3d851c300f24) | 确认应用侧返回了上游服务不可用的 HTTP 错误码 |
| 3 | Logging | elasticsearch | Pattern: `dependency unavailable, http_status: 503, path: /work` (occurrence_count: 16) | 业务日志证实应用内部处理依赖请求时失败 |
| 4 | Tracing | Deepflow L7 Flow | `GET /work` from `172.16.104.55` to `172.16.104.35`, response_code: 503 (fact-858f043c6099 等) | 网络层记录确认了发起探测/请求的源 IP 及持续 503 响应事实 |
| 5 | K8s State | kubelet | Pod `status: Running`, container `restart_count: 0` (fact-a95d0764f12a, fact-05c0c927de34) | 排除容器崩溃、重启导致进程未启动的可能性 |
| 6 | K8s Config | K8s Config | `container: app, resource_request.memory: 24Mi, resource_limit.memory: 96Mi` (fact-305fb49b1f97, fact-41233a4cc874) | 排除因内存限制导致的 OOMKilled |

**证据关联与印证说明：**
1. Kubernetes 事件中的 TCP 连接拒绝（证据 1）与 503 错误（证据 2）共同指向同一个 IP `172.16.104.35` 的 8080 端口服务异常。
2. 日志证据（证据 3）与 Trace 数据（证据 4）从应用内部视角确认了该异常并非网络层阻断，而是应用尝试访问依赖资源后收到了 503 状态码。
3. 状态和配置证据（证据 5、6）排除了 Pod 自身生命周期异常（如 CrashLoopBackOff）或资源配额问题（OOM），将故障原因收敛至依赖资源不可用。

## 🎯 根因分析 · g1

### 因果链

```text
外部依赖资源不可用（连接被拒） → 应用返回 HTTP 503 → Readiness Probe 探测持续失败 → Pod 状态维持 NotReady
```

### 根因结论

**已确认的根因：Pod 依赖的外部资源（监听在 172.16.104.35:8080 的服务）不可用。**

- **依据：** 诊断明确由 kubelet 报告 `dial tcp ... connect: connection refused`（证据 1）引起，且伴随应用侧返回 `HTTP 503`（证据 2、3、4）。
- **现象：** Readiness Probe 持续探测失败，导致 Pod 进入 `NotReady` 状态。
- **排除：** Pod 自身处于 `Running` 状态且无重启（证据 5），内存配置正常（证据 6），故排除应用进程崩溃或资源限制问题。

**说明：** 根因指向外部依赖服务本身（目标 IP `172.16.104.35`）的健康状态。当前证据仅确认了该 IP 的探测/连接失败，未提供该依赖服务具体的集群内标识（如 Service 或 Deployment 名称）供进一步定位，但该事实已足以解释当前的 Pod 故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.4s
├─ 并发证据采集: 95.5s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 95.5s (Evidence 89.4s, RCA 5.9s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
