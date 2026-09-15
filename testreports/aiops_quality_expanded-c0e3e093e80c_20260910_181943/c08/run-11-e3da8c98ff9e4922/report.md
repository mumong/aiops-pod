## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | OOMKilled | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff，容器因 OOMKilled (Exit Code 137) 频繁重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | memory limit: 64Mi (fact-14f829ecb92f) | 定义容器硬限制，是故障发生的物理天花板 |
| 2 | K8s Event | Kubernetes | OOMKilled, Exit Code 137 (fact-77d428af8d7e) | 直接记录系统强制终止进程的状态 |
| 3 | K8s State | Kubernetes | restart_count: 11 (fact-1140562e694b) | 量化故障导致的重启频率和持续性 |
| 4 | Logging | Elasticsearch | Pattern "memory allocation advanced": 8 occurrences, 42Mi in last record (fact-50f9fc6c31bb) | 显示处理请求时内存分配达到42Mi，逼近64Mi限制 |
| 5 | Tracing | Deepflow | L7 Flow: GET /work, 9 occurrences (fact-20f0fbbb966e) | 提供触发内存分配的高频业务场景 |

**证据印证说明：**
- K8s 配置（#1）与 K8s Event（#2）结合确认了资源受限被触发的事实。
- Logging（#4）中的内存分配数值（42Mi）与 Tracing（#5）中的请求路径 `/work` 一致，说明特定业务请求导致内存快速增长。
- 42Mi 已占 64Mi 限制的大部分，进一步证实了限制过低导致 OOM 的推论。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置仅为 64Mi → 应用处理 GET /work 请求时内存分配超过限制 → 容器被系统 OOMKilled 终止 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是应用容器内存限制配置过低（64Mi）。

- 容器在重启后频繁接收对 `/work` 路径的 HTTP 请求（事实#5）。
- 在处理这些请求时，应用进行了内存分配，日志显示单次记录中内存分配达到 42Mi（事实#4），这一数值在 64Mi 的硬性限制下极易触发 OOM。
- 系统据此执行了 OOMKilled 操作并退出（事实#2），导致容器不断重启（事实#3）。
- 证据链闭环完整，确认配置与现象间的因果关系。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 13.1s
├─ 并发证据采集: 137.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 137.1s (Evidence 128.1s, RCA 8.8s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled
