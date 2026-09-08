## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 (namespace: aiops-case-04) 持续处于 CreateContainerConfigError 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | waiting_message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认 Pod 启动前校验阶段因缺少 Secret key 失败 |
| 2 | K8s State | K8s | waiting_reason: `CreateContainerConfigError` | 判定异常类型为配置类错误，阻碍容器启动 |
| 3 | K8s Event | K8s | Normal Pulled 3m58s (x326 over 73m): Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine | 证明镜像拉取及网络底层 CNI 初始化正常，排除镜像或网络故障 |
| 4 | K8s State | K8s | pod.phase: `Pending` | 确认 Pod 当前状态未进入 Running |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `CreateContainerConfigError`, timestamp: `2026-09-03T09:09:47.922000Z`) | 监控指标与 Kubernetes 事件状态一致，确认错误持续时间较长 |

**证据互证说明：**
Kubernetes 事件 (fact-36c28c91e6c0, fact-3a1f5d4daa5e) 明确指出因 Secret key 缺失导致 `CreateContainerConfigError`；Metric (fact-30ebdcf1ea00) 独立观测到了相同的错误类型状态，佐证了故障的持续性和稳定性；同时，事件中的镜像拉取记录证明集群基础运行环境（镜像、网络插件）正常，排除了其他基础设施因素。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 错误引用 Secret key 'unavailable-key' (fact-36c28c91e6c0)
→ Kubernetes 容器启动前置检查：在 Secret 'aiops-case-04/workload-input' 中未找到目标 key
→ kubelet 抛出 CreateContainerConfigError，阻断容器创建 (fact-3a1f5d4daa5e)
→ Pod 持续处于 Pending / CreateContainerConfigError 状态，无法运行 (fact-23d11915529a, fact-3c424572e761)
```

### 根因结论

**已确认的根因：** 异常组 `g1` 的 Pod `workload-6584f97c76-wvcb2` 启动失败，是因为其配置引用了 Secret `aiops-case-04/workload-input` 中的 `unavailable-key`，但该 key 实际并不存在于目标 Secret 中。

这一配置错误直接触发了 Kubernetes 的 `CreateContainerConfigError` 机制，导致 kubelet 无法完成容器配置校验，从而使 Pod 始终停留在 `Pending` 状态。该结论由 K8s State (fact-36c28c91e6c0, fact-3a1f5d4daa5e) 的明确报错原文直接支撑，且被 Metric 数据 (fact-30ebdcf1ea00) 证实为长期持续状态，证据链完整。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 23.5s
├─ 并发证据采集: 72.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 72.2s (Evidence 62.2s, RCA 9.8s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
