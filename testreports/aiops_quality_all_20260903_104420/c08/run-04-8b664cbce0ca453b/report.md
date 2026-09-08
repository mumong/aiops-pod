## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod容器内存限制配置过低（64Mi），无法支撑应用在处理/work请求时的内存分配需求，导致容器因内存超限被OOMKilled并陷入CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container: `app`, reason: `OOMKilled`, exit_code: `137` | 确定进程终止直接原因为内存超限被杀 (Fact IDs: fact-ea3cfddc615d, fact-d26f4ef3f248) |
| 2 | K8s Config | kubernetes | container `app` memory limit: `64Mi`, request: `24Mi` | 确立触发 OOM 的资源约束条件 (Fact IDs: fact-80dd38d8f804, fact-1b1bd1dd62ce) |
| 3 | Logging | elasticsearch | Pattern `http_request` 8 occurrences, path `/work`; memory `allocated_mib` from `14` to `46` (Fact IDs: fact-82b0af5a3d2b...) | 展示应用在处理请求时存在内存分配增长行为，且已逼近 64Mi 限制 (Fact IDs: fact-82b0af5a3d2b...) |
| 4 | Tracing | tempo/deepflow | Spans & Flows `GET /work` returning `200`; observed_mode `oom_growth` (Fact IDs: fact-bf4f74394c2a, fact-20826a5e8cc7...) | 提供流量上下文，确认内存分配增长与特定业务接口 `/work` 强相关 (Fact IDs: fact-bf4f74394c2a, fact-20826a5e8cc7...) |

**证据说明：**
- Kubernetes 维度的 OOMKilled 状态、日志中的内存增长趋势与 Tracing 中的 OOM 观测模式互为印证，形成闭环：应用请求 `/work` 时内存分配逐渐增加，最终触发 64Mi 硬性限制导致进程被内核 OOM Killer 终止。

## 🎯 根因分析 · g1

### 因果链

```text
Pod容器内存限制配置过低（64Mi） → 应用处理 `/work` 请求时内存分配需求超过Limit → 触发OOM Killer终止进程(Exit 137) → Pod持续重启并陷入CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
容器 `app` 的内存配置（Limit: 64Mi）过低，无法支撑其在处理 `/work` 请求时的动态内存分配需求，导致容器频繁被 OOMKilled 并进入 CrashLoopBackOff 状态。
**证据支持：**
- [K8s State] 显示容器最后终止原因为 `OOMKilled` (fact-ea3cfddc615d)，退出码 `137` (fact-d26f4ef3f248)。
- [K8s Config] 显示容器内存 Limit 仅为 `64Mi` (fact-80dd38d8f804)。
- [Logging] 显示处理 `/work` 请求时内存分配从 14Mi 增长至 46Mi (fact-82b0af5a3d2b)。
- [Tracing] 在对应流量的 Span 中记录了 `oom_growth` 模式 (fact-bf4f74394c2a)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.1s
├─ 并发证据采集: 57.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 57.3s (Evidence 49.0s, RCA 8.1s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
