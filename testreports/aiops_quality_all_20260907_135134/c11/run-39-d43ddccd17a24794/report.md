## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 被施加了自定义 finalizer `aiops.lab/hold`。Kubernetes 删除机制要求必须清除该 finalizer 后才会真正删除 Pod 对象，但没有任何控制器释放它，导致 Pod 对象被无限期挂在 Terminating 状态（当前已持续 67 分钟）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | phase: Running, status: Terminating (lasts 67m) [fact-5c4ce5239cba] | 核心现象：Pod 处于不可用状态，且持续时间长。 |
| 2 | K8s Event | Pod Events | `cni.projectcalico.org/podIPs:`, `cni.projectcalico.org/podIP:` 等网络状态注解记录 [fact-0fb03663466c] | 证明 Pod 对象已被调度且网络插件已完成相关配置，但容器本身无法恢复。 |
| 3 | K8s State | Container Exit | last_terminated_reason: Error, exit_code: 137 [fact-05227edd5893], [fact-430b0fc838bd] | 容器已因 SIGKILL 终止，137 号退出码表示被系统强制停止，非正常退出。 |
| 4 | K8s State | Pod Conditions | ContainersReady: False (ContainersNotReady), Ready: False [fact-491d60c04ff5], [fact-e382422f5d50] | 确认容器未就绪且 Pod 处于终止流程中，无法提供服务。 |
| 5 | Metric | Restart Count | kube_pod_container_status_restarts_total: 0 [fact-6ca69edd9040] | 排除因资源不足导致的 OOM 重启循环（restart=0），与 exit code 137 及 Terminating 状态一致。 |

上述证据链显示，Pod 虽然拥有有效的网络配置（Calico IP），但容器进程已被强制终止（exit 137）且无重启。Kubernetes 的 Terminating 状态表明删除请求已发出但卡住，结合诊断信息，说明删除阻塞并非由于资源竞争或容器崩溃重启，而是由于 finalizer 机制被锁定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含自定义 finalizer `aiops.lab/hold` 且未被移除 → 强制阻止 Pod 删除 → 容器已终止但对象保留在 Terminating 状态 (67m) → 服务不可用
```

### 根因结论

**已确认根因**：Pod `aiops-case-11/workload` 被施加了自定义 finalizer `aiops.lab/hold`，且没有任何控制器释放它，导致 Pod 对象无限期停留在 Terminating 状态。
- **证据支撑**：诊断信息明确指出 finalizer `aiops.lab/hold` 的存在及其对删除机制的阻塞作用 [诊断描述]；容器退出码 137 及 67 分钟的 Terminating 状态证实了非正常终止与卡死现象 [fact-5c4ce5239cba, fact-05227edd5893, fact-430b0fc838bd]；Kubernetes 事件记录了网络插件（Calico）相关的状态，表明 Pod 生命周期曾正常启动，但后续被阻止清除 [fact-0fb03663466c]。

**未知项/证据不足**：
- 注册 `aiops.lab/hold` finalizer 的具体 Controller 或 Operator 组件身份。
- 该 Controller 未释放 finalizer 的业务或技术原因。
由于缺少 Logging 和 Tracing 数据 [logging: absent, tracing: absent]，且工具采集报告明确指出 Topology 查询失败 [missing_reasons: observability-gate-1-topology...]，无法进一步定位触发 finalizer 注册或导致其无法释放的具体应用行为或控制器日志。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.5s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-11/workload: 41.5s (Evidence 34.1s, RCA 7.3s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
