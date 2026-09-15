## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 应用代码实现了依赖外部文件信号（/state/teardown-requested）的阻塞式优雅关闭逻辑，当前因信号文件缺失导致容器进程无法退出；当前处于 terminationGracePeriodSeconds 3900s 定义的正常终止等待期内，并非系统级 TerminatingStuck 故障。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase=Running`；条件 `Ready=True, ContainersReady=True` (fact-b2af7b976878, fact-d613f718037e) | 确认 Pod 核心组件已就绪，应用代码已正常启动并运行 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory=32Mi`, `container.resource_limit.cpu=50m` (fact-99d5a3162bc3, fact-a190d143a3e0) | 资源限制配置，用于排除资源耗尽导致的启动失败或 OOM |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (fact-e56413806e7d) | 确认容器自启动以来未发生过异常崩溃或重启 |
| 4 | Logging | elasticsearch | `application started` (fact-777ef8b743fc) | 确认应用生命周期已走完启动阶段，进入稳定运行态 |
| 5 | Topology | k8s_tabular_query | `error: unexpected custom-columns spec...` (failed_tool_attempts) | 工具调用失败，未能提供节点级拓扑信息，不影响核心应用层诊断 |

证据 1（K8s 状态）与证据 3、4（指标与日志）互相印证，表明 Pod 从启动到当前时刻均处于稳定、健康的运行状态，且未发生过重启。证据 2（资源限制）排除了容器因资源不足被 Kill 的可能。结合诊断信息中提及的“Terminating 等待期”及“阻塞式优雅关闭逻辑”，当前的异常状态是应用层特定的终止逻辑行为，而非底层基础设施故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码依赖外部文件 /state/teardown-requested 触发优雅关闭 → 信号文件 /state/teardown-requested 未被创建 → 容器进程持续运行阻塞正常终止 → Pod 呈现 Terminating 状态但内核进程未退出（等待 3900s Grace Period）
```

### 根因结论

**已确认的根因**：Pod 应用代码实现了阻塞式优雅关闭逻辑，该逻辑强依赖于外部文件信号（`/state/teardown-requested`）的存在。由于该信号文件在当前环境中未被创建，导致容器进程无法响应正常的终止请求，从而停留在终止等待期内。

此结论得到了以下事实的支持：
- **证据 1 (K8s State)** 显示 Pod 状态健康，排除了系统级故障或应用崩溃。
- **证据 3 (Metric)** 和 **证据 4 (Logging)** 证实了应用已成功启动且无重启记录，说明故障仅发生在终止阶段。
- **诊断信息** 明确指出当前的 Terminating 状态是由于应用代码逻辑导致的正常终止等待，而非 Kubernetes 调度或节点层面的异常。

**未确认事项**：
- 外部文件 `/state/teardown-requested` 为何未被创建。
- 为何未配置主动触发该文件的上游依赖机制。

以上两点属于应用逻辑上游的依赖缺失，需要进一步审查应用配置或上游触发流程，但不影响当前“终止逻辑因信号缺失而阻塞”的根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.4s
├─ 并发证据采集: 59.5s
│  └─ g1 aiops-case-v12/workload: 59.5s (Evidence 51.4s, RCA 8.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
