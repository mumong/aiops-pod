## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | Pod aiops-case-10/workload-79d9f8fd88-48j8r 因 Liveness Probe 失败触发重启，当前处于 Running 但 history 中存在 exitCode 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-6e98ab772a6e) | 确认 Liveness Probe 失败，直接触发后续重启行为。 |
| 2 | K8s Event | kubelet | `Container app failed liveness probe, will be restarted` (fact-bd1ddaa58eff) | 证明 kubelet 已按策略执行 Killing 动作。 |
| 3 | K8s State | Pod Status | `Exit Code: 137` (fact-44289409ca8d) | 历史退出码 137 强关联 OOMKilled 或 SIGKILL。 |
| 4 | K8s Config | Resources | `Limit Memory: 96Mi` (fact-36c372fa6bec), `Request Memory: 24Mi` (fact-6600f044aae9) | 提供硬限制资源上限，结合 Exit Code 137 支持资源受限推断。 |
| 5 | Tracing | Tempo / Deepflow | `GET /work` 响应 200, Trace `ecf8d05c65cea2e98b57404f22cf3f26` (fact-5285a2074d6c) | 证明核心业务接口 `/work` 健康，限定了故障仅在 Probe 端或内部处理延迟。 |

证据表明：容器虽然运行中且业务接口（/work）返回 200，但因 Liveness Probe 返回 HTTP 500 被 kubelet 判定为不健康并执行重启（fact-1, 2）。重启历史中存在 Exit Code 137（fact-3），且容器内存硬限制仅为 96Mi（fact-4）。结合 Trace 显示业务请求正常（fact-5），故障具有间歇性或局部性，核心现象由 Liveness Probe 失败触发重启，Exit Code 137 暗示了可能的底层资源压力。

## 🎯 根因分析 · g1

### 因果链

```text
容器资源受限 / 突发延迟 → Liveness Probe 返回 HTTP 500 → Kubelet 执行 Killing → 容器重启 (exitCode 137)
```

### 根因结论

已确认的根因是 **Liveness Probe 配置的检查机制与容器响应能力不匹配**。

具体而言，Kubelet 检测到容器对 Liveness Probe 返回 HTTP 500（证据 1），判定容器健康状态异常并执行 Kill 操作（证据 2）。在此过程中，容器曾以 Exit Code 137 终止（证据 3），结合 96Mi 的内存硬限制（证据 4），高度指向内存超限（OOMKilled）或系统级资源压力导致进程响应缓慢，进而引发 Probe 超时或 500 错误。

证据不足之处：
- **OOM 确认度**：输入中 `execute_pod_promql` 因 `namespace` 缺失报错（`query_parse_failed`），且 `unknowns` 指出 `container_memory_working_set_bytes` 数据被截断。因此，目前无法 100% 区分 Exit Code 137 是确切由 OOMKilled 引起，还是其他导致 SIGKILL 的系统级原因，但资源受限是最高概率场景。
- **Probe 内部日志**：日志主要覆盖 `/work` 路径且 HTTP 200（证据 5），缺乏 Probe 端点（如 `/health`）返回 500 时的具体应用层错误日志，无法排除 Probe 端点实现错误的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 19.2s
├─ 并发证据采集: 100.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 100.6s (Evidence 85.9s, RCA 14.6s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime
