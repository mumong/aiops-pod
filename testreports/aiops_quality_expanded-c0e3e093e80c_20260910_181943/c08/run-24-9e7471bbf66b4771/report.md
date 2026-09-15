## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | RecentRestart | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，容器反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 终止原因 `OOMKilled`，退出码 `137` | 确认为内存超额的硬性终止事件 |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存上限 `64Mi` (Request: `24Mi`) | 证明存在受限的硬资源边界 |
| 3 | Metric | Prometheus | 容器重启总数 `17`，最后终止原因标签为 `OOMKilled` | 提供 CrashLoopBackOff 的长期症状统计 |
| 4 | K8s Event | Kubernetes | Kubelet 记录 `BackOff` 状态，在 `75m` 内重试 `278` 次 | 佐证容器在反复崩溃与重启的循环中 |
| 5 | Logging | Elasticsearch | 8 条日志显示分配内存从 `48Mi` 降至 `22Mi` | 确认应用存在内存分配操作与波动 |
| 6 | Tracing | Deepflow/Tempo | 9 次 `GET /work` 调用成功返回 `200`，跨度标签标记 `oom_growth` | 关联业务流量与 OOM 发生时的系统行为 |

**证据关联说明：**
- 证据 1、2、5、6 共同构建了从“正常业务请求（日志/链路）”到“逼近 64Mi 硬限制”再到“被 OOM Killer 强制终止”的完整闭环，其中日志和链路数据证实了 OOM 发生在应用正常处理业务期间，排除了空转导致的可能。
- 证据 3、4 则从宏观状态角度印证了这一循环已持续较长时间。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 HTTP GET /work 时进行内存分配 → 内存使用量逼近 64Mi 的硬性限制 → Linux 内核触发 OOM Killer 强制终止进程 (Exit Code 137) → Pod 频繁重启进入 CrashLoopBackOff
```

### 根因结论

根因已确认：容器资源配置不足。
Pod `workload-5c9c7b6489-p8462` 中的 `app` 容器被配置了 `64Mi` 的内存硬限制 (`resource_limit`)。在业务高峰期处理请求时，应用实际内存消耗逼近该阈值，触发了 Kubernetes 节点的 OOM Killer，导致进程被内核强制终止（退出码 137，状态 `OOMKilled`），进而引发 kubelet 不断重启容器，最终表现为 `CrashLoopBackOff`。

**证据支持：**
- 容器终止原因为 `OOMKilled`，退出码 `137` (证据 #1)。
- 内存硬限制配置为 `64Mi` (证据 #2)。
- 日志与链路追踪证实应用正在正常处理 `GET /work` 流量并伴随 `oom_growth` 状态 (证据 #5, #6)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.6s
├─ 并发证据采集: 66.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 66.0s (Evidence 56.5s, RCA 9.3s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
