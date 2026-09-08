## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | {'message': 'Annotations:      cni.projectcalico.org/containerID: 2435240c99025fff4535fb5b94e7ab812eb06657e15bafa2551f90c470883192'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-1166acb9cdc8) | 确认应用健康检查接口直接返回 503 错误 |
| 2 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` (fact-666f24b18384) | 反映探针曾遭遇底层网络连接拒绝，佐证服务进程不活跃 |
| 3 | Logging | elasticsearch | `dependency unavailable` (fact-5a1e0cc5160e 等)；8 次记录；时间窗口 `18:04:51 - 18:05:17` | 确认应用在处理 `/work` 请求时检测到上游依赖故障 |
| 4 | Tracing | deepflow (HTTP Flow) | `GET /work` 返回 503，连接 `172.16.104.19` → `172.16.104.26` (fact-5a0e422f0500 等) | 在应用 IP 上复现了相同的 503 状态码，验证了 503 并非偶发 |
| 5 | Tracing | tempo (Span) | `GET /work` trace_id: `d882babe0b383bda1a35dd7116d979a4` (fact-0dac21718955) | 将特定追踪请求与日志/流量数据的时间戳与异常关联 |
| 6 | K8s State | kubelet | `pod.status: Running` (fact-b051beae00a2)；`restart_count: 0` (fact-7a272fb25bb2) | 排除容器崩溃重启导致的间歇性不可用 |
| 7 | K8s Config | kubelet | `container.resource_limit.memory: 96Mi` (fact-a21115441ff5) | 资源限制已存在，但日志中 `allocated_mib` 均为 0，暂无法归因于 OOM |

**证据分析：**
1、2 号 K8s 事件证实探针持续失败且包含早期的连接拒绝错误，但 Pod 始终处于 Running 且无重启（6号证据），说明应用进程本身在运行。3、4 号证据（日志与流量）将故障时间点精确锚定在 `18:04 - 18:05`，确认应用处理业务请求 `/work` 时因“上游依赖不可用”返回了 503，这与探针（5号证据）观测到的状态一致。然而，日志未能指明具体的下游服务（如数据库或缓存），导致 3号证据在根因定位上存在断层。

## 🎯 根因分析 · g1

### 因果链
```text
上游依赖服务响应失败或不可用（未确认具体实体） → 应用检测到依赖故障并返回 503 (HTTP 503 'dependency unavailable') → Readiness 探针接收 503 状态码持续失败 → Pod 状态变为 NotReady，服务不可接入
```

### 根因结论
已确认根因为：应用在处理请求时遭遇上游依赖服务故障，导致接口持续返回 HTTP 503，进而触发 Kubelet 健康检查失败。
- 证据链支持：日志中连续出现 `dependency unavailable` 错误（证据 3），且流量数据确认了相同的 503 响应（证据 4）。
- 根因局限：现有事实仅停留在应用层的“依赖不可用”断言，**缺少决定性事实**以确认具体是哪个下游服务（例如数据库、缓存或第三方 API）导致了故障。由于 `published` 被配置为 `false`，无法关联更深层的绑定数据，需进一步调查以获取完整的调用拓扑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 24.2s
├─ 并发证据采集: 95.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 95.9s (Evidence 86.2s, RCA 9.6s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
