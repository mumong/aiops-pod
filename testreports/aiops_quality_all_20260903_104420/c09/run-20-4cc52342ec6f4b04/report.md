## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 状态为 NotReady (ContainersNotReady)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` | 初期探针探测 TCP 连接被拒绝，表明应用进程未就绪或端口无监听 |
| 2 | K8s Event | `kubelet` | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 持续探针报错 HTTP 503，表明应用进程已启动但返回了业务级错误 |
| 3 | K8s State | `Pod` | `ContainersReady=False` (`ContainersNotReady`) | 确认 Pod 处于 `NotReady` 状态，因容器 `app` 未就绪 |
| 4 | Logging | `elasticsearch` | `pattern: "dependency unavailable", http_status: 503, path: "/work"` (共 8 次) | 提供应用侧视角：应用逻辑因依赖不可用主动返回 503 |
| 5 | Tracing | `deepflow (L7 Flow)` | `GET /work`, `dst_ip: 172.16.104.26`, `response_code: 503` (共 9 次) | 流量层面证实对 Pod IP 的请求持续被拒绝，且响应码为 503 |
| 6 | K8s Config | `container` | `memory.request: 24Mi`, `memory.limit: 96Mi` | 资源配额较低，排除因资源超限导致崩溃（无重启记录） |

证据 1 和 2 共同描绘了从“端口无响应”到“返回 503”的异常状态演变；证据 4（日志）和证据 5（流量）在 HTTP 层面相互印证，证实 503 状态码由应用逻辑主动返回，而非网络或 kube-proxy 层面的故障。

## 🎯 根因分析 · g1

### 因果链

```text
未验证的上游依赖不可用 → 应用逻辑返回 HTTP 503 'dependency unavailable' → 就绪探针检测非 200 状态码失败 → Pod 状态转为 NotReady (ContainersNotReady)
```

### 根因结论

已确认的根因是**应用逻辑因依赖服务不可用而主动返回 HTTP 503 错误**。
应用代码在依赖（如数据库、缓存等）不可用时，按照设计返回了 503 状态码。Kubernetes 就绪探针（Readiness Probe）探测 `/ready` 接口时，捕获到了该 503 错误，认为容器未准备好，从而将 Pod 状态置为 `ContainersNotReady`。

目前证据链在应用层已闭环（日志与流量均指向“dependency unavailable”），但缺乏具体依赖组件的状态证据，无法确认是配置错误、依赖组件宕机还是网络隔离导致依赖不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 26.0s
├─ 并发证据采集: 80.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 80.9s (Evidence 72.6s, RCA 8.2s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
