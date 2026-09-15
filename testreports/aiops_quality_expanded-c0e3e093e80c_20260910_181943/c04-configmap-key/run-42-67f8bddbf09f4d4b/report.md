## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 处于 Waiting 状态，报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-2cfc91ea44b9` | container `app` waiting reason: `CreateContainerConfigError` | 确认异常状态为配置注入阶段失败 |
| 2 | K8s Event | `fact-40d3cb2d520a` | Warning Failed: `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接指出具体的缺失资源键名及目标 ConfigMap |
| 3 | K8s State | `fact-f176defe026a` | container `app` waiting message: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 验证 kubelet 具体的失败原因，与 Event 一致 |
| 4 | K8s State | `fact-325048717980` | pod phase: `Pending` | 确认 Pod 整体不可用，处于等待状态 |
| 5 | Metric | `fact-30d3ea46bfe5` | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"}` = `1` | 从监控指标维度独立确认了 Pod 卡在配置错误阶段 |
| 6 | Metric | `fact-bb755eaf1b63` | `kube_pod_container_status_restarts_total{container="app"}` = `0` | 证明容器未发生过运行，直接排除了运行时崩溃重启的可能 |

**证据互证：** 证据 #1、#2、#3 在 Kubernetes 控制平面与 Event 中形成了闭环，明确指出了是 `ConfigMap` 中缺少 `unavailable-key` 导致无法创建容器。证据 #4 确认了该错误导致的直接宏观后果（Pending）。证据 #5 提供了 Prometheus 监控视图下的同一确认，且 #6 的重启计数为 0 排除了其他导致等待的干扰因素（如 CrashLoopBackOff）。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 key 'unavailable-key' → kubelet 无法完成配置注入 → 容器启动失败并处于 Waiting 状态 (CreateContainerConfigError) → Pod 卡在 Pending 阶段，无法对外提供服务
```

### 根因结论
已确认的根因是 Pod 定义中存在无效配置。Pod 尝试从 ConfigMap `aiops-case-v11/workload-input` 注入名为 `unavailable-key` 的数据，但该键在 ConfigMap 中不存在。这直接触发了 `CreateContainerConfigError`（证据 #2、#3），导致容器无法启动并一直处于 `Waiting` 状态（证据 #1、#5），且从未发生过重启（证据 #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.9s
├─ 并发证据采集: 37.9s
│  └─ g1 aiops-case-v11/workload: 37.9s (Evidence 30.1s, RCA 7.7s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
