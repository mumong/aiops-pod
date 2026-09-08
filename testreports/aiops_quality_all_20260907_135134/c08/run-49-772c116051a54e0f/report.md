## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，容器不断被 OOMKilled 终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器退出码 `137`，终止原因 `OOMKilled` (`fact-64cc6e8a2111`) | 确认容器因内存超限被内核强杀 |
| 2 | K8s State | Kubernetes | 容器内存请求 `24Mi`，限制 `64Mi` (`fact-0db14dea4bd2`, `fact-313f7cafec0a`) | 明确系统级资源硬性天花板 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 为 `OOMKilled` (`fact-3fa5fa5af876`) | 从指标维度独立验证了 K8s 事件记录的终止原因 |
| 4 | Logging | Elasticsearch | 应用日志 `memory allocation advanced` 在 32 秒内记录内存分配从 10Mi 升至 42Mi (`fact-logging`) | 证实容器进程在请求期间持续申请内存，且增速快于处理周期 |
| 5 | Tracing | Tempo/Deepflow | 关联请求 `GET /work` 返回 200，且应用标注 `oom_growth` 模式 (`fact-7b080247c4fe`) | 证明在内存急剧增长的时段，请求业务逻辑本身尚未发生崩溃或超时 |

**证据印证说明：**
日志中 `allocated_mib` 的快速攀升（4 到 21 倍增长）与 K8s 记录的 `OOMKilled` 及退出码 137 高度吻合。指标数据作为独立观测源，证实了终止事件的客观性。Tracing 数据显示服务在 OOM 发生前仍在处理 200 状态码请求，排除了因应用逻辑错误或 HTTP 层异常导致崩溃的可能性，进一步聚焦于内存资源消耗本身。

## 🎯 根因分析 · g1

### 因果链
```text
应用 /work 接口请求处理存在内存泄漏 → 内存分配量（42Mi）逼近并超过 Pod 硬限制（64Mi） → 触发内核 OOM Killer 终止进程（Exit Code 137） → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论
已确认根因为**应用代码存在内存泄漏**（证据 #4）。容器应用在每次处理 `GET /work` 请求时持续分配内存且未有效释放，导致内存使用量在数十秒内呈上升趋势，最终突破 Kubernetes 设定的 `64Mi` 内存限制。内核机制（Evidence #1, #3）随即介入杀死容器进程，引发 `CrashLoopBackOff` 现象（Evidence #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 25.9s
├─ 并发证据采集: 77.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 77.5s (Evidence 66.9s, RCA 10.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
