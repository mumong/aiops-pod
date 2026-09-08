## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l status NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接触发 Pod 进入 NotReady 状态的原因 |
| 2 | K8s Event | kubernetes | `Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 证实应用服务在宿主机 IP 及端口上无法建立连接 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` | 证明异常发生以来应用容器未发生重启，故障处于持续未修复状态 |
| 4 | Metric | prometheus | `kube_pod_status_phase(phase=Unknown)=0` 且 `phase=Running=1` | 确认 Pod 处于 `Running` 阶段，但处于 `NotReady` 状态 |
| 5 | Logging | elasticsearch | `http_status=503`, `path=/work`, `service=aiops-lab-workload` (时间窗: 19:08:53 - 19:09:29) | 证实应用在处理请求时主动向客户端返回 503 状态码 |
| 6 | Tracing | deepflow | `HTTP GET /work` 返回 `response_code=503` (src_ip: 172.16.104.55 → dst_ip: 172.16.104.35) | 独立网络流量数据再次印证了 503 错误的存在 |

**证据印证说明**：K8s 探针日志（#1, #2）直接反映了应用服务在 8080 端口拒绝连接或返回 503，这与应用自身的日志输出（#5）及下游客户端的追踪数据（#6）完全吻合，确认了应用服务健康检查失败是持续发生的确定性事件。Metric 监控（#3, #4）排除了容器因 OOM 或 Crashing 导致重启的可能，进一步锁定问题在于应用内部的依赖或逻辑，而非容器实例本身的生命周期异常。

## 🎯 根因分析 · g1

### 因果链

```text
上游依赖不可用/应用逻辑异常（未确认） → 健康检查端点返回 503 且拒绝连接 → Readiness Probe 持续失败 → Pod 状态标记为 NotReady
```

### 根因结论

已确认的根因机制是：**应用就绪探针（Readiness Probe）持续失败，导致 Pod 被 Kubernetes 判定为 `NotReady`。**

具体表现为：
1. 探针访问 `http://172.16.104.35:8080/ready` 时，底层连接被拒绝（`connection refused`）或收到 `HTTP 503` 响应。
2. 这一现象并非容器重启导致，且应用在处理常规请求（`/work`）时也返回 503。

**证据不足**：
正式报告中指出根因是“上游依赖不可用（Upstream dependency unavailable）”，但当前事实缺乏决定性证据：
1. **依赖身份不明**：日志中仅记录了 `dependency unavailable`，未指出具体是数据库、缓存还是其他第三方服务。
2. **连接拒绝原因未知**：探针报 `connection refused` 既可能是应用进程崩溃后未完全退出（尽管未重启，但进程可能僵死），也可能是应用正在启动中，或者是防火墙/安全组拦截。
3. **503 源头不明**：应用返回 503 是由于自身代码逻辑主动拒绝，还是因为它依赖的某个关键服务宕机而主动降级？缺乏该下游依赖的日志或指标支撑。

因此，现有证据只能支撑到“应用服务状态异常导致探针失败”，无法证实是具体的哪一个上游依赖导致了此次故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.5s
├─ 并发证据采集: 66.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 66.8s (Evidence 57.8s, RCA 8.9s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed, pod-crashloop-runtime, pod-imagepull-failed, pod-config-error
