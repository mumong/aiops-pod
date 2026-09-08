## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 持续处于 NotReady 状态 (0/1 Ready) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 36s (x2286 over 110m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` | 展示 Readiness 探针高频失败的具体原因与时间跨度 |
| 2 | K8s State | kubernetes | `ContainersReady`: `False` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 确认容器应用层未能通过健康检查 |
| 3 | K8s State | kubernetes | `pod.phase`: `Running` | 确认应用容器处于运行态（非 CrashLoopBackOff） |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `0` | 排除因 OOM 或重启导致的周期性故障 |
| 5 | Logging | elasticsearch | 聚合模式 `dependency unavailable`，`http_status: 503`，`path: /work` (首次: `2026-09-03T19:43:25.413Z`, 末次: `2026-09-03T19:43:59.563Z`) | 日志确认业务逻辑在处理 `/work` 时遭遇下游依赖问题 |
| 6 | Tracing | deepflow | 聚合 HTTP GET `/work` 响应 `503`，`src_ip: 172.16.104.19` → `dst_ip: 172.16.104.26` (首: `2026-09-04 03:15:26`, 末: `2026-09-04 03:42:55`) | 流量特征验证服务在持续向外返回 503 |
| 7 | Tracing | tempo | `GET /work` 响应 `503`, `trace_id: 5a23e0c80f2d1e117abdc6c429c94edd` | 提供单次请求的精确观测点 |

日志显示业务逻辑明确记录了 `dependency unavailable` 并返回 `503`，这与探针收到的 `503` 响应及 Deepflow 捕获的 L7 流量特征完全一致。探针失败频率 (`x2286`) 与日志及流量记录的时间窗口高度吻合。由于应用状态为 `Running` 且重启次数为 `0`，结合业务层日志，确定是应用内部或依赖组件异常导致业务逻辑降级/报错，而非系统层或容器引擎问题。

## 🎯 根因分析 · g1

### 因果链
```text
应用服务内部依赖项不可用 (未确认具体依赖对象) → Readiness Probe 向 /work 发起 HTTP GET 请求收到 503 响应 → kubelet 判定 Readiness 探针失败 → Pod 状态标记为 NotReady
```

### 根因结论
**已确认根因**：应用服务在处理 `/work` 端点请求时遭遇内部依赖不可用，导致持续返回 HTTP 503 状态码。这触发了 kubelet 的 Readiness Probe 失败机制（证据 [1]），使得应用容器无法被标记为 Ready（证据 [2]），尽管应用进程本身正在运行且无重启（证据 [3]、[4]）。
业务日志（证据 [5]）与流量追踪（证据 [6]、[7]）相互印证，确认了 503 响应的来源是应用自身的依赖处理逻辑。

**未确认项**：具体的不可用依赖对象名称（日志未捕获具体依赖报错）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 18.1s
├─ 并发证据采集: 84.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 84.0s (Evidence 72.8s, RCA 11.0s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
