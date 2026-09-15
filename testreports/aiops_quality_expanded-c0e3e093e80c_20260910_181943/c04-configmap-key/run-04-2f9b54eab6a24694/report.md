## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod workload (aiops-case-v11) stuck in CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: app 容器处于 `CreateContainerConfigError` (fact-23ff6053f90d) | 确认应用容器因配置问题处于等待状态，无法进入运行态 |
| 2 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-27a35b60014a) | 精确指出 Pod 规范在挂载 ConfigMap 时，找不到指定的 key |
| 3 | K8s Event | kubernetes | `Warning Failed` (x12 over 12m): `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-a172c9e9adb6) | 提供 kubelet 重试失败的明确证据，表明故障是持续性的 |
| 4 | K8s State | kubernetes | `pod.phase`: Pending (fact-338b02500eab) | 确认 Pod 未处于 Running 或 Succeeded 状态 |
| 5 | K8s Config | kubernetes | `container.resource_request.cpu`: 5m, `resource_limit.cpu`: 50m, `resource_request.memory`: 8Mi, `resource_limit.memory`: 32Mi (fact-158c745fba10, fact-468328476c9c, fact-9dfb18561b86, fact-9551a652c5dc) | 提供容器资源申请上下文，排除资源超卖导致的状态异常 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 (fact-a36015083293) | 通过独立观测源确认容器等待原因为 `CreateContainerConfigError`，与 K8s 事实一致 |

**证据印证说明：**
1. K8s 状态与事件的 `waiting_reason` (fact-23ff6053f90d) 和 `waiting_message` (fact-27a35b60014a) 提供了故障的直接定义和详细参数，Metric (fact-a36015083293) 独立验证了该等待原因为 `CreateContainerConfigError`。
2. Event (fact-a172c9e9adb6) 记录了 12 分钟内 12 次失败的 kubelet 重试，证实了这是持续性配置故障而非瞬时网络问题。
3. 资源配置 (fact-158c745fba10 等) 和 Pod 处于 Pending 状态 (fact-338b02500eab) 说明故障发生在容器创建/资源绑定阶段，尚未涉及 CPU 或内存超卖，日志与追踪数据因容器未启动而无数据，符合预期。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用了不存在的 ConfigMap key 'unavailable-key' (fact-27a35b60014a, fact-a172c9e9adb6) → Kubelet 在容器创建阶段无法解析该挂载项 → 容器创建失败，状态标记为 CreateContainerConfigError (fact-23ff6053f90d, fact-a36015083293) → Pod 始终处于 Pending 状态，服务不可用 (fact-338b02500eab, fact-2b106afd94ab)
```

### 根因结论
**已确认的根因：** Pod 规范（`aiops-case-v11/workload`）中定义了对 ConfigMap `aiops-case-v11/workload-input` 中 key `unavailable-key` 的引用，但该 key 在 ConfigMap 中不存在，导致 Kubelet 无法完成容器创建。

**支持依据：**
- **K8s 事实与事件：** `container.waiting_message` (fact-27a35b60014a) 和 `Warning Failed Event` (fact-a172c9e9adb6) 明确指出 "couldn't find key unavailable-key"。
- **Metric 独立观测：** `kube_pod_container_status_waiting_reason` (fact-a36015083293) 将等待原因记录为 `CreateContainerConfigError`，证实了配置错误的严重性。

**未知/需确认项：**
- 无法确认 ConfigMap `aiops-case-v11/workload-input` 是完全缺失，还是存在但该 key 未定义。现有证据仅指出引用的 key 缺失，未提供 ConfigMap 整体存在性的独立事实（如 `kubernetes.state.get_configmap` 等工具未返回相关事实，或该信息在收集中被截断/未命中）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 12.6s
├─ 并发证据采集: 556.7s
│  └─ g1 aiops-case-v11/workload: 556.7s (Evidence 549.3s, RCA 7.2s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
