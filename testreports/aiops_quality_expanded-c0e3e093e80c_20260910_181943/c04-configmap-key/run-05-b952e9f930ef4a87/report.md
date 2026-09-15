## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 CreateContainerConfigError 状态，容器未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `app` 容器 `waiting_reason`: CreateContainerConfigError | 确认 Pod 停留在创建配置阶段的直接异常状态 |
| 2 | K8s Event | Pod Status | `app` 容器 `waiting_message`: "couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" | 直接定位缺失的具体配置项与 ConfigMap 名称 |
| 3 | K8s State | Pod Phase | `phase`: Pending, `ContainersNotReady` | 证实容器始终无法进入 Running 状态 |
| 4 | K8s State | Container Resources | Memory `request`: 8Mi, `limit`: 32Mi; CPU `request`: 5m, `limit`: 50m | 资源限制数值合理，排除 OOMKill 或资源不足导致的状态异常 |
| 5 | K8s State | Container Status | `restart_count`: 0 | 排除因应用崩溃重启导致的状态异常 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (app) = 1 (reason: CreateContainerConfigError) | 从时序指标侧印证容器处于特定的配置错误等待状态 |

**证据说明：**
K8s 原生状态（#1, #2）给出了决定性的失败原因：ConfigMap 中缺失指定的 key。K8s 异常状态（#3, #4, #5）排除了资源竞争或容器存活率等干扰因素。Prometheus 指标（#6）与 K8s 原生报错信息完全一致，相互印证了故障的单一性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key` → 
ConfigMap 数据校验/挂载检查失败 → 
Kubelet 抛出 CreateContainerConfigError 阻止容器创建 → 
Pod 状态保持 Pending，应用未启动
```

### 根因结论

已确认根因：**Pod 配置引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`**（证据 #1, #2）。

该错误导致 kubelet 在初始化容器阶段无法获取所需的配置数据，从而直接触发 `CreateContainerConfigError`，使得容器未能启动且 Pod 维持在 Pending 状态。证据 #6 中的时序指标进一步验证了这一配置错误的持久性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.1s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-v11/workload: 41.5s (Evidence 32.5s, RCA 8.9s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
