## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 Pending 状态，容器 app 报告 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (x12 over 7m44s) | 直接证明 Kubelet 因无法定位 Secret Key 而持续拒绝创建容器 |
| 2 | K8s State | kubelet | 容器 `app` 等待原因为 `CreateContainerConfigError` | 确认容器因配置（Secret 引用）问题处于创建阻塞状态 |
| 3 | K8s State | kubelet | Pod 阶段为 `Pending`；`ContainersReady` 和 `Ready` 状态均为 `False` | 确认 Pod 整体停留在启动前的阻塞阶段 |
| 4 | K8s Config | kubelet | 资源请求/限制已配置 (CPU: 5m/50m, Mem: 8Mi/32Mi) | 排除资源配额不足导致的调度或启动延迟 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 为 `1` (Label: reason=`CreateContainerConfigError`) | 指标侧独立确认了容器处于配置错误等待状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 `0` | 证实容器从未成功运行过，无重启现象 |

**证据说明：**
1、2 号证据在 Kubernetes API 层面形成了完整的因果闭环：Event 记录了具体的失败动作（找不到 key），State 记录了该动作导致的容器状态（`CreateContainerConfigError`）。
5 号 Metrics 证据独立确认了容器的等待原因，与 K8s State 证据完全一致，排除了单一数据源偏差。
4、6 号证据排除了资源争抢和容器反复崩溃重启等可能性，将故障焦点锁定在容器创建阶段的配置校验环节。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'workload-input' 仅包含 key 'available-key'，缺少 'unavailable-key' 
→ Pod 配置引用了不存在的 'unavailable-key' 
→ kubelet 创建容器时无法找到指定的 Secret Key 
→ 容器创建失败 (CreateContainerConfigError)，Pod 处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod Spec 配置了不存在的 Secret Key**。

Kubelet 在尝试启动 `workload-6584f97c76-wvcb2` 的 `app` 容器时，发现 Pod 模板中引用了 `Secret aiops-case-04/workload-input` 下的 key `unavailable-key`，但该 Secret 对象实际并不包含此 key（证据 #1, #2）。这一配置错误直接触发了 `CreateContainerConfigError` 状态，导致容器无法创建且 Pod 长期处于 `Pending` 阶段。现有的 Kubernetes 状态与 Metrics 数据已充分支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.7s
├─ 并发证据采集: 64.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 64.0s (Evidence 53.6s, RCA 10.1s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
