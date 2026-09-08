## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Ready=False, message: containers with unready status: [app] (fact-02b6d7664166, fact-bc216e61fd2a) | 直接表征 Pod 处于不可服务状态 |
| 2 | K8s Event | kubernetes | Readiness probe failed: dial tcp 172.16.104.26:8080/ready: connection refused (fact-68e95d7b1eef); statuscode: 503 (fact-6ae1215dc458) | 探测机制直接报错，连接拒绝与 HTTP 503 交替出现 |
| 3 | Logging | elasticsearch | 聚合日志模式 `dependency unavailable`，http_status=503，path=/work (fact-103b104836e0) | 证实应用内部逻辑在处理依赖时发生阻断并对外返回 503 |
| 4 | Tracing | deepflow+tempo | Flow: src=172.16.104.19 -> dst=172.16.104.26, HTTP GET /work -> 503 (fact-132812f93a47) | 网络流量数据在 L7 层复现了探测失败与日志报错的同一现象 |

证据链表明：探测机制（K8s Event）在 172.16.104.26:8080 收到失败响应，这直接导致 Pod 状态标记为 NotReady。深层观测确认了 Pod 内部在 /work 接口处理请求时，因“依赖不可用”而主动抛出 503，这与追踪日志中捕获的 HTTP 流量及应用日志完全吻合，证明了外部不可达性源于应用内部对上游依赖的故障处理。

## 🎯 根因分析 · g1

### 因果链

```text
Application dependency unavailable → Readiness Probe HTTP 503 → ContainersNotReady → Pod NotReady
```

### 根因结论

已确认的根因为**应用依赖不可用导致就绪探针（Readiness Probe）连续失败**。
依据：
- K8s Event 与 Tracing 数据显示应用端点（172.16.104.26:8080）对外返回 503 并伴随连接拒绝；
- Logging 事实明确指出错误根源在于 `dependency unavailable`。

未确认部分：日志中仅提示“依赖不可用”，未提供具体的下游服务名或根本源头（如网络中断、上游故障或配置错误），因此具体的故障起点待进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 18.0s
├─ 并发证据采集: 111.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 111.2s (Evidence 103.8s, RCA 7.2s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
