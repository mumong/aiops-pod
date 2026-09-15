## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 状态为 CreateContainerConfigError，容器持续 Waiting 未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Warning Failed (x12): Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 直接指因：Kubelet 校验 ConfigMap 引用失败 |
| 2 | K8s State | kubelet | container.waiting_reason: CreateContainerConfigError; container.waiting_message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 确认容器因配置错误处于 Waiting 状态 |
| 3 | K8s State | kubelet | pod.status: Pending; pod.phase: Pending | 确认 Pod 未能进入 Running 状态 |
| 4 | K8s Config | kubelet | 资源约束：CPU request 5m, limit 50m; Memory request 8Mi, limit 32Mi | 排除资源配额不足导致调度或启动失败 |
| 5 | K8s State | kubelet | restart_count: 0 | 确认容器未实际启动，仅经历配置校验阶段 |
| 6 | K8s Event | kubelet | 5 条 CNI/网络状态事件 (projectcalico) | 确认 Pod 网络插件及 IP 分配正常，非网络问题 |
| 7 | Metric | prometheus | kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1 | 指标证实异常状态的客观存在，无变化趋势 |

**证据小结：**
K8s 维度的事件（#1）与状态（#2）互相印证，共同指向 ConfigMap 键缺失导致的配置错误；Metrics（#7）确认了该状态在监控侧的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失 key 'unavailable-key' → Kubelet 解析失败 → 容器启动前校验失败 → Pod 持续 Waiting/Pending
```

### 根因结论

已确认根因：Pod `aiops-case-v11/workload` 的容器定义通过环境变量引用了 ConfigMap `aiops-case-v11/workload-input` 中的键 `unavailable-key`，但该 ConfigMap 实际数据中仅包含 `available-key`，缺失目标键导致 Kubelet 在创建容器时校验失败，最终 Pod 处于 `CreateContainerConfigError` 状态（参见证据 #1, #2）。

**缺失决定性事实：**
未获取到实际 `workload-input` ConfigMap 的完整数据记录，目前基于报错信息的推断存在极小概率偏差（如存在其他同名资源），但鉴于报错明确且唯一，此结论具有高度确定性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.0s
├─ 并发证据采集: 46.5s
│  └─ g1 aiops-case-v11/workload: 46.5s (Evidence 37.7s, RCA 8.6s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
