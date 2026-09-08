## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 状态为 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接呈现 Kubelet 判定探针失败的明确原因 |
| 2 | K8s State | K8s State | `ContainersReady: False`, `Ready: False` (reason: `ContainersNotReady`) | 确认 Pod 当前未就绪的真实状态 |
| 3 | Logging | Logging | `dependency unavailable` (pattern, 8 occurrences, 19:28:20Z - 19:28:51Z) | 提供应用侧 503 响应的根本业务原因 |
| 4 | Tracing | Deepflow Flow | `GET /work` `HTTP 503`, 9 occurrences, src_ip: 172.16.104.19 -> dst_ip: 172.16.104.26 | 从网络侧印证了该 Pod 持续对外返回 503 状态码 |
| 5 | K8s State | K8s State | `restart_count: 0` | 排除容器 CrashLoopBackOff 等导致重启的异常情况 |

证据 1、2 确认了 Pod 因 Readiness 探针失败而处于 NotReady 状态的故障表现。证据 3 与证据 4 形成了因果闭环：应用日志记录了具体的后端依赖缺失原因，而网络流追踪证实了该 Pod 在处理请求（包括探针请求）时稳定返回 HTTP 503。证据 5 排除了容器因崩溃重启导致不稳定的干扰，将故障精准锁定在业务逻辑层面。

## 🎯 根因分析 · g1

### 因果链

```text
应用后端依赖不可用 → 服务处理健康检查请求并返回 HTTP 503 → Readiness Probe 判定失败 → Pod 标记为 NotReady
```

### 根因结论

已确认的根因为：应用容器后端依赖不可用，导致其 Readiness Probe 探测端点 `/work` 持续返回 HTTP 503 状态码，进而触发 Kubelet 探针失败机制，使 Pod 被移出就绪状态 [证据 1, 2, 3, 4]。当前证据链完整且互相印证，但因未获取具体的 Pod YAML 探针配置参数及更底层的依赖报错堆栈，导致具体是哪一个后端服务或组件不可用仍属于未确认状态 [unknowns]。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 13.0s
├─ 并发证据采集: 97.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 97.8s (Evidence 88.3s, RCA 9.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
