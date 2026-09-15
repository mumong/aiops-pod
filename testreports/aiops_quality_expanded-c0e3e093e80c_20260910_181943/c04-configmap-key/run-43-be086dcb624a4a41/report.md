## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的 Spec 中引用了 ConfigMap `aiops-case-v11/workload-input` 中的 key `unavailable-key`，但该 ConfigMap 中实际仅包含 key `available-key`，导致 Kubelet 在创建容器时找不到指定 key，从而触发 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-1abb6188c63f) | container "app" waiting reason: `CreateContainerConfigError`；message: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接揭示 Kubelet 因找不到 ConfigMap key 而拒绝创建容器的原因 |
| 2 | K8s State | kubernetes (fact-7cd8166e778f) | pod `aiops-case-v11/workload` phase: `Pending` | 确认 Pod 因配置错误始终处于 Pending 状态，未能进入运行态 |
| 3 | K8s State | kubernetes (fact-049b91bbe146) | pod condition `ContainersReady` = `False`；message: `containers with unready status: [app]` | 确认容器未就绪，与 CreateContainerConfigError 状态一致 |
| 4 | Metric | prometheus (fact-c8890929ad22) | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"}` = `1` | 从监控指标独立验证了容器当前确实处于该等待原因 |
| 5 | Metric | prometheus (fact-c247b1a78864) | `kube_pod_container_status_restarts_total{container="app"}` = `0` | 确认容器尚未发生过重启，故障停留在配置加载阶段 |

**证据说明：**
1. 容器指标（#4）明确显示等待原因为 `CreateContainerConfigError`，与 Kubelet 状态（#1）完全一致，确认故障性质为配置加载失败。
2. Pod 状态指标（#1 中的 K8s State）与指标（#4）互证，说明 Pod 卡在 Pending 阶段是由于容器引擎无法完成初始化，且重启计数为 0（#5），排除了运行期 CrashLoopBackOff 的可能性。
3. 日志与追踪均为 `not_applicable`，符合容器因配置错误无法启动、不产生业务日志的事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 ConfigMap key (unavailable-key) → Kubelet 解析 Pod 配置失败 (CreateContainerConfigError) → 容器无法启动，Pod 状态保持 Pending → 应用不可用
```

### 根因结论

已确认根因为 **Pod `aiops-case-v11/workload` 的 Spec 中引用了 ConfigMap `aiops-case-v11/workload-input` 中的 key `unavailable-key`，但该 ConfigMap 实际仅包含 key `available-key`** [证据 #1]。

这一配置错误导致 Kubelet 在尝试创建容器时发现必需数据缺失，直接触发 `CreateContainerConfigError` [证据 #1, #4]。由于错误发生在容器启动前的配置加载阶段，容器不会进入 Running 状态，因此不会发生重启（重启计数为 0）[证据 #5]，Pod 持续保持在 `Pending` 状态 [证据 #2]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.7s
├─ 并发证据采集: 35.8s
│  └─ g1 aiops-case-v11/workload: 35.8s (Evidence 28.1s, RCA 7.6s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
