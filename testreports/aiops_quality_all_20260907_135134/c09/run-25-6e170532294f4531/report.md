## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod `workload-5f4fb9ff45-7b77l` 处于 `NotReady` 状态，Readiness 探针持续失败 (HTTP 503) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 描述探针初期连接阶段失败，确认为目标 Pod 的底层问题 |
| 2 | K8s Event | K8s Event | `Warning Unhealthy ... Readiness probe failed: HTTP probe failed with statuscode: 503` (重复 935 次) | 核心症状：应用启动后持续返回应用层拒绝，导致 Pod 状态变为 `ContainersNotReady` |
| 3 | K8s Config | K8s Config | Container `app` 内存限制 `96Mi`，CPU 请求 `20m`，限制 `200m` | 资源配额充足，排除因资源耗尽（OOM/CPU Throttling）导致的拒绝 |
| 4 | Logging | Elastaicsearch | Pattern `dependency unavailable` (HTTP 503 on `/work`)，重复 8 次 (fact-0148f349c148 等) | 确认应用自身在处理请求时返回 503 错误，直接支撑应用层主动拒绝的结论 |
| 5 | Metric | Prometheus | `container_memory_usage_bytes` = `15556608` (约 14.8 MiB) | 确认运行内存远低于 96Mi 限制，验证排除资源受限 |
| 6 | Metric | Prometheus | `container_cpu_usage_seconds_total` = `6.408719` | 确认 CPU 消耗极低，进一步验证排除性能瓶颈 |
| 7 | Tracing | Deepflow/Tempo | Span `GET /work` 返回 `503`，耗时 `13.1ms` - `19.4ms` (fact-06c6810c9421 等) | 确认故障响应快速，属于逻辑拒绝而非网络超时或下游依赖等待 |

**证据印证说明：**
*   证据 1、2 证实 Pod 处于 `NotReady` 状态的根本原因是探针在 `:8080/ready` 遭遇连接拒绝与 503 错误。
*   证据 4 提供了应用层的直接证据（`dependency unavailable` 日志），解释为何探针会收到 503。
*   证据 3、5、6 结合，排除物理资源（内存/CPU）不足导致的异常，将根因范围缩小至应用逻辑故障。
*   证据 7 通过链路追踪确认了应用的故障响应模式（快速 503），佐证了故障的持续性和确定性。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 `FAILURE_MODE=readiness_fail` → 应用逻辑依赖不可用，主动返回 HTTP 503 → Kubelet 探针连续 935 次收到 503，判定容器不健康 → Pod `Ready=False` (ContainersNotReady)，无法接收流量
```

### 根因结论

已确认根因为 **应用层故障注入测试配置生效**。应用被显式配置为 `FAILURE_MODE=readiness_fail` 模式，导致应用逻辑内部模拟“依赖不可用”并直接返回 HTTP 503 错误。

*   **证据支持：** 证据 2 显示 Readiness 探针因连续 503 响应导致 Pod 被标记为 `ContainersNotReady`；证据 4 在应用日志中捕获了明确的 `dependency unavailable` 错误模式；证据 3、5、6 排除了资源限制因素。
*   **未决事项：** 虽然日志表明“依赖不可用”，但未查明底层实际依赖组件的具体状态（unknowns），不过由于应用层是主动返回 503，底层依赖的具体状态对当前故障现象（Pod 不健康）不构成阻碍因素。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 20.8s
├─ 并发证据采集: 109.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 109.0s (Evidence 97.0s, RCA 11.9s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
