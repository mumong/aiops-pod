## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'Initialized', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `phase: Running`, `ContainersReady: True`, `Ready: True`, `PodScheduled: True` (fact-1b582764e373 ~ fact-99e006dfb49f) | 确认 Pod 内部逻辑与网络状态完好，与 Terminating 状态形成明显异常对比 |
| 2 | K8s Config | Kubernetes | `app container memory limit: 32Mi`, `cpu limit: 50m` (fact-50b46bffcc17, fact-b29187d5c2a8) | 提供资源边界上下文，排除因资源超限导致的 OOM 或 CPU 节流 |
| 3 | K8s State | Kubernetes | `container.app restart_count: 0` (fact-cc6b990b5874) | 排除应用频繁崩溃重启导致 Terminating 状态异常的可能 |
| 4 | Logging | Elasticsearch | `application started` (fact-8ec0f8c16c20) | 证实应用已正常启动，但未记录到终止期相关的日志输出 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total{container="app"}: 0` (fact-21dbb9b0acb0) | 指标与 K8s State 一致，进一步确认运行平稳且无重启发生 |
| 6 | Tracing | Deepflow/Tempo | 无数据 (status: absent) | 缺失链路追踪数据，无法确认终止请求的到达路径及处理细节 |

**证据交叉分析：**
- 证据 1 (K8s 状态) 与证据 4/5 (日志/指标) 共同证实应用处于“完美运行”的活跃状态，没有任何崩溃或资源争用的迹象。
- 这种应用内部的“活跃”与 K8s 层面的“终止中”状态不一致，通常由 `preStop` 钩子卡死、存储卷卸载缓慢或外部强杀（HardKill）前的宽限期等待引起。由于缺少证据 6 (Tracing) 以及 Bash 探查文件存在性失败，导致无法判断是应用逻辑阻塞还是底层基础设施延迟。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被触发 Terminating (deletionTimestamp) → Kubelet 发送 Killing 信号 (等待 3900s 宽限期) → 终止状态卡死 (应用状态却显示为 Running) → 应用逻辑未执行完毕、未执行 PreStop、或存储卷卸载卡死 → 用户可见：Pod 长期保持 Terminating 状态
```

### 根因结论

**证据不足**。
现有事实证实了应用内部在终止期间仍保持 `Running` 状态且未重启，但无法确定终止过程中的具体阻塞点。

主要缺失的关键事实包括：
1. **缺乏 PreStop Hook 证据**：无相关日志 (Fact 4 缺失) 或 Tracing 数据 (Fact 6 缺失)，无法判断 Hook 是否执行、执行耗时或是否被卡住。
2. **缺乏文件/存储状态探查结果**：用于排查应用依赖文件（如 `/state/teardown-requested`）的工具执行失败 (Input validation error)，且缺失 Topology 查询结果，导致无法确认应用是否因“找不到预期文件”而卡住。
3. **缺乏宽限期内的状态变化**：3900秒宽限期内无日志记录，无法区分是等待钩子完成还是等待底层挂载卷卸载完成。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.8s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-v12/workload: 46.2s (Evidence 36.5s, RCA 9.7s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
