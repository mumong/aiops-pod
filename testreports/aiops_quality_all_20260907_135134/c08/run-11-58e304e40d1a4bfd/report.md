## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff... Back-off restarting failed container app... Reason: OOMKilled, Exit Code: 137` | 直接证明容器因内存超限被系统杀死并反复重启。 |
| 2 | K8s Config | Kubernetes | `resource_limit.memory: 64Mi` | 定义导致 OOMKilled 的硬性限制边界。 |
| 3 | Logging | Elasticsearch | Pattern: `memory allocation advanced`, allocated_mib first=10 -> last=46 (17:02:22 - 17:02:58) | 证实应用在执行内存分配时发生持续且快速的增长，逼近 64Mi 限制。 |
| 4 | Tracing | Deepflow/Tempo | Flow: `GET /work`, status: 200, span: `aiops.observed_mode: oom_growth` | 关联日志中的内存分配行为发生在特定 API 请求期间，确认内存增长是由业务负载触发。 |

证据印证逻辑：K8s 状态确认了 **OOMKilled** 和 **Exit Code 137** 的终止原因（证据1）；K8s 配置确立了 **64Mi** 这一低门槛限制（证据2）；而日志中的 **内存从 10Mi 增至 46Mi** 的增长轨迹（证据3）配合 Tracing 对 `/work` 路径的 **oom_growth** 观测（证据4），闭环说明了是 `/work` 接口的内存分配行为直接触发了硬限制导致崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置内存硬限制 64Mi → /work 接口处理请求导致内存分配增长(10Mi->46Mi) → 使用量突破 64Mi 触发 OOMKilled → CrashLoopBackOff
```

### 根因结论

已确认的根因为 **容器内存配置过低**。Pod 中 `app` 容器被设置了 `64Mi` 的硬内存限制，在处理 `/work` 端点请求时，应用进行内存分配导致内存使用量在短时间内显著增长（日志记录从 10Mi 增长至 46Mi），最终突破系统硬性限制。内核触发 **OOMKilled** 机制并返回 `Exit Code: 137`，进而导致 Kubernetes 反复重启容器，表现为 `CrashLoopBackOff`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 28.5s
├─ 并发证据采集: 62.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 62.5s (Evidence 52.8s, RCA 9.6s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
