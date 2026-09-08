## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | {'message': 'Annotations:      cni.projectcalico.org/containerID: 2435240c99025fff4535fb5b94e7ab812eb06657e15bafa2551f90c470883192'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady=False`, `Ready=False`, 原因: `ContainersNotReady`, 信息: `containers with unready status: [app]` (fact-4f2180bcc745, fact-dd30a560e90b) | 确认 Pod 处于运行但就绪失败的异常状态 |
| 2 | K8s Event | kubernetes | Readiness probe failed: `HTTP probe failed with statuscode: 503` (fact-5f789bffaa41, fact-9d2de83f886c) | 直接故障现象：应用层就绪检查未通过 |
| 3 | K8s Event | kubernetes | Readiness probe failed: `dial tcp 172.16.104.26:8080: connect: connection refused` (fact-e34b7c5552b6, fact-f2e20d65b353) | 早期现象：探针尝试连接 8080 端口时被拒绝 |
| 4 | Metric | prometheus | `container_memory_working_set_bytes` 当前值 `15433728` Bytes (约 14.7MB) (fact-09780f4929d6) | 排除内存超限：实际使用量（14.7MB）远低于 Limit 96Mi |
| 5 | Logging | elasticsearch | 日志模式 `dependency unavailable`, `http_status: 503`, `path: /work` (fact_ids: fact-41e805d93bda 等), `trace_ids`: 10 个 (如 fcf07867e9c56567974d8262b1649fac) | 核心根因线索：应用返回 503 并明确报错缺少依赖 |
| 6 | Tracing | deepflow | HTTP GET `/work` 返回 `503`, `src_ip: 172.16.104.19` → `dst_ip: 172.16.104.26`, `duration_us`: 17953~30628 (fact-5a0e422f0500 等) | 确认从 Pod IP 出发的 /work 请求确实返回 503 |

证据表明 Pod 处于 NotReady 状态，探针经历从“连接拒绝”到“返回 503”的转变。应用日志中多次出现 `dependency unavailable` 导致 `/work` 路径返回 503 的情况，同时 Tracing 数据确认了该路径请求的真实失败。内存指标处于正常低位，排除了 OOM 导致应用无响应的可能。但日志中并未明确指出是哪一个具体的服务/资源“不可用”，且 `/ready` 探针同样失败的原因尚未在事实中解释（日志仅聚合了 /work 的失败）。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的服务/资源不可用 → Readiness Probe 探测端点返回 503 (HTTP probe failed) → 容器未通过就绪检查 (ContainersNotReady) → Pod 状态 NotReady
```

### 根因结论

**已确认的根因：**
Pod 应用进程无法提供正常的就绪服务。K8s 就绪探针（Readiness Probe）探测 Pod IP (172.16.104.26) 的 8080 端口，早期表现为 `connection refused`，随后应用进程启动但业务逻辑返回 `HTTP 503` 错误，具体日志显示 `dependency unavailable`（见证据 5、6）。应用进程运行正常（非 OOM 或 CrashLoop），但因依赖不可用而无法通过就绪检查。

**证据不足与未知：**
正式 RCA 中明确标注 `diagnostic_status: inconclusive`。目前事实仅能证明“依赖不可用”这一抽象结果，但缺少以下决定性事实：
1. **具体依赖实体不明**：日志中只记录了 `dependency unavailable` 模式，未包含导致该错误的上游服务名称或具体资源标识（如数据库、缓存、其他微服务）。
2. **探针行为逻辑不明**：日志聚合仅针对 `/work` 路径的 503，而 K8s 事件中 `/ready` 探针同样失败（包括早期的连接拒绝），应用为何在依赖不可用时连 `/ready` 也无法成功响应，其内部逻辑联系尚不清晰。

---

## 📊 性能统计

```text
├─ 总耗时: 3.4m
├─ 问题定位: 18.8s
├─ 并发证据采集: 171.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 171.3s (Evidence 162.5s, RCA 8.5s)
└─ 汇总总结: 15.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
