## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod workload in aiops-case-v11 namespace stuck in Pending state with CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes (Pod) | status: Pending; container restart_count: 0 | 确认 Pod 处于未运行状态且未发生重启。 |
| 2 | K8s Event | Kubernetes (kubelet) | Warning Failed: "Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" (12 times over 24m) | 指出 Pod 无法启动的直接失败原因及缺失的 ConfigMap 键名。 |
| 3 | Metric | Prometheus | kube_pod_container_status_waiting_reason=1 (label: CreateContainerConfigError) | 量化验证了当前处于配置错误的等待状态。 |
| 4 | Metric | Prometheus | kube_pod_container_status_restarts_total=0 | 从指标层面佐证了容器未能启动，无重启行为。 |

**证据印证说明：**
Kubernetes 事件（#2）给出了明确的失败细节（找不到键 `unavailable-key`），这与 Waitting 原因（#3）完全吻合。两者共同证实了容器因环境配置错误（ConfigMap key 缺失）而无法拉起，进而导致 Pod 停留在 Pending 状态且无重启（#1, #4）。日志与追踪维度因容器未启动被标记为 `not_applicable`，属正常现象。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 'unavailable-key' 数据项 → Pod Spec 引用该不存在的键进行配置注入 → kubelet 在容器创建阶段解析失败 (CreateContainerConfigError) → 容器无法拉起，Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 规范中引用了 ConfigMap `aiops-case-v11/workload-input` 中名为 `unavailable-key` 的键，但该键在 ConfigMap 中实际不存在（证据 #2, #3）。这直接导致 kubelet 在启动容器时因无法解析环境变量或挂载数据而返回 `CreateContainerConfigError`。

**未知项**：现有证据仅证明了键缺失的事实，无法判定是 Pod 规范中存在拼写错误，还是 ConfigMap 中的数据被意外删除。

---

## 📊 性能统计

```text
├─ 总耗时: 49.9s
├─ 问题定位: 17.7s
├─ 并发证据采集: 24.6s
│  └─ g1 aiops-case-v11/workload: 24.6s (Evidence 17.5s, RCA 6.9s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
