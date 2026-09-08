## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: OOMKilled (app) | 直接事实：内核因内存溢出终止容器。 |
| 2 | K8s Config | Kubernetes | container.resource_limit.memory: 64Mi (app) | 根本配置：容器被严格限制在 64Mi 内存内。 |
| 3 | Logging | Elasticsearch | Pattern: `memory allocation advanced`, allocated_mib first=10, last=48 | 趋势佐证：应用处理请求期间内存持续快速增加。 |
| 4 | Tracing | Deepflow | 9条 HTTP GET /work 流量记录，response_code=200 | 业务场景：崩溃前的正常业务流量触发资源消耗。 |

上述证据链互相印证：Deepflow 记录了请求处理（#4），Elasticsearch 日志显示在请求期间内存持续攀升（#3），最终导致应用突破 Kubernetes 设定的 64Mi 硬限制（#2），被 OOM Killer 强制终止（#1）。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制过低 (64Mi) → 应用处理请求时内存突破限制 → OOM Killer 终止进程 (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

**已确认根因：容器内存资源限制配置过低（64Mi）。**
Kubernetes 配置中 `container.resource_limit.memory` 为 64Mi (#2)。在业务请求期间（#4），容器内存持续增长至 48Mi（#3），最终突破限制。内核 OOM Killer 随即强制终止应用（#1），导致 Pod 不断重启并进入 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.4s
├─ 并发证据采集: 59.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 59.6s (Evidence 51.7s, RCA 7.8s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
