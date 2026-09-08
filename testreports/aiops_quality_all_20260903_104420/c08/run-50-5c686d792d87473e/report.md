## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 容器内存限制过小（64Mi）导致应用在高负载下触发OOMKilled并持续崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137; Reason: OOMKilled | 直接证明容器因内存超限被杀 |
| 2 | K8s State | kubernetes | container.resource_limit.memory = 64Mi | 确认触发 OOM 的硬限制阈值 |
| 3 | K8s Event | kubernetes | BackOff restarting failed container app | 证实 OOMKilled 后的持续崩溃重启循环 |
| 4 | K8s Config | kubernetes | container.resource_request.memory = 24Mi | 排除 Request 不足，确认为 Limit 过小 |
| 5 | Metric | prometheus | container_memory_working_set_bytes: 55,431,168 字节 (约 52.8Mi) | 峰值内存逼近 64Mi 硬限制，逼近致死边界 |
| 6 | Metric | prometheus | container_memory_working_set_bytes: 30Mi → 55Mi (窗口内) | 展示内存随请求处理的持续攀升趋势 |
| 7 | Logging | elasticsearch | `allocated_mib` 从 12 攀升至 36; pattern: "memory allocation advanced" | 确认内存增长与 `/work` 处理过程强相关 |
| 8 | Tracing | deepflow | `GET /work` HTTP 200, 9次重复, duration 15-24ms | 证明高负载下应用持续处理请求导致内存增长 |

**证据说明：**
1. **配置边界**：Memory Limit 仅为 64Mi（Fact 2），而 Request 为 24Mi（Fact 4），说明资源申请宽松但限制极紧。
2. **触发机制**：Metrics（Fact 5, 6）显示应用内存从 30Mi 攀升至 52.8Mi，逼近 64Mi 硬限制。
3. **直接原因**：Log（Fact 7）指出在处理 `/work` 时发生内存分配增长，Tracing（Fact 8）证明该接口高并发访问。
4. **最终现象**：容器突破 64Mi 边界触发 OOM Killer（Fact 1），导致 Pod 进入 CrashLoopBackOff（Fact 3）。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低（64Mi） → 高并发处理 /work 请求时内存持续攀升 → 突破硬限制触发 K8s OOM Killer → 容器退出码 137 崩溃并重启
```

### 根因结论

**根因已确认**：容器资源限制配置不合理。

1. **硬限制过小**：`container.resource_limit.memory` 配置为 **64Mi**（证据 2）。
2. **内存增长超出限制**：在高负载下，应用在处理 `/work` 请求时内存从约 30Mi（证据 6）持续攀升至约 52.8Mi（证据 5），并伴随显式内存分配（证据 7）。
3. **OOM 触发**：由于可用内存空间被耗尽，应用突破 64Mi 硬限制触发 Kubernetes OOM Killer，进程以退出码 137 被终止（证据 1）。
4. **持续故障**：Pod 因频繁 OOMKilled 进入 CrashLoopBackOff 状态（证据 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 26.7s
├─ 并发证据采集: 86.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 86.9s (Evidence 78.5s, RCA 8.2s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
