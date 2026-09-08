## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | RecentRestart | Pod workload-79d9f8fd88-sbqvc 处于 RecentRestart 状态，频繁异常终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`="Error"; `container.last_exit_code`=137 | 确认容器最近一次终止的原因为错误且退出码为 137（通常对应被系统信号终止） |
| 2 | K8s State | kubernetes | `container.restart_count`=47 | 证实 Pod 处于频繁重启的状态 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`="96Mi"; `container.resource_limit.cpu`="200m" | 提供容器资源硬限制上限，用于后续评估是否发生内存溢出 (OOMKilled) 的基础数据 |
| 4 | K8s Config | kubernetes | `container.resource_request.memory`="24Mi" | 提供容器资源预留请求量，反映该业务对资源的预期占用情况 |
| 5 | K8s State | kubernetes | `pod.phase`="Running" | 显示 Pod 目前阶段为运行中，处于重启后的恢复状态 |
| 6 | Tracing | deepflow+tempo | `http.response.status_code`=200; `duration_us` min/max: 17581.0~112125.0; `aiops.observed_mode`="liveness_fail" | 证明请求成功响应且耗时在毫秒级，但观测模式记录为 Liveness Fail，说明容器是在服务层正常响应后由 kubelet 触发的终止 |

**证据关联说明：**
1-2 组事实确立了容器频繁因异常终止而重启的现象；3-4 组事实提供了关键的硬件边界数据（200m CPU / 96Mi 内存），为评估资源耗尽提供了参照；5 组事实确认了当前 Pod 是活跃状态；6 组 Tracing 数据证实了应用业务层本身是健康且可响应的，但存在 `liveness_fail` 事件记录，这为将故障机制定位在 Kubelet 探针层面而非应用代码错误提供了直接证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行在 Alpine 镜像上，CPU资源极度受限 → Liveness Probe 请求 /work 端点响应时间超过阈值导致 liveness_fail → Kubelet 执行 Kill 动作使容器退出码变为 137 → Pod 频繁重启 (restarts=47)
```

### 根因结论

**证据不足**。

尽管 `K8s State` 中的 `last_terminated_reason`="Error" 和 `exit_code`=137 与 Kubelet 终止行为高度吻合，且 Tracing 证据确认了 `liveness_fail` 事件，但**现有输入事实中缺失决定性的 `OOMKilled` 直接证据或内存监控指标**。

1. 事实 `fact-0d56e4261d08` 仅显示终止原因为 `Error`，而非 `OOMKilled`。虽然 Exit 137 常伴随 OOM，但在资源限制仅 96Mi 且未提供 Memory Working Set Metric (Metrics absent) 的情况下，无法排除其他导致 137 退出的可能。
2. 提供的正式 RCA 声称“OOMKilled”，但这依赖于未展示或未通过验证的隐藏事实（如提示中的 `fact-e8d9781cb5fb`，该事实 ID 在输入的真实事实清单中不可见）。
3. 由于输入规则严格限制只能使用可见的真实数据，且 Metrics 维度为空，无法提供内存使用趋势数据来印证是否触达 96Mi 限制。

因此，虽然现象是 Liveness Probe 失败导致被 Kill，但断言其为 OOM 引发的失败机制属于**证据不足**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.3s
├─ 并发证据采集: 52.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 52.9s (Evidence 44.3s, RCA 8.3s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled
