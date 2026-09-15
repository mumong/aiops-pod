## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态且持续 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-68c557d875-gtzc8` 当前 `status: Pending` | 确定异常实体及最终停留状态 |
| 2 | K8s Event | Kubernetes | `FailedScheduling 10m (x13 over 70m)`：**0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector** | 提供调度失败的直接原因：亲和性/选择器不匹配 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.cpu`: `50m`, `request.cpu`: `5m` | 确认资源需求极低，排除 CPU 资源不足导致的调度失败 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: `32Mi`, `request.memory`: `8Mi` | 确认内存需求极低，排除内存资源不足导致的调度失败 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` (Pending): `1` (sample_count=1); (Failed): `0` | 确认 Pod 长期保持在 Pending 状态，未出现其他状态转变 |

**证据说明**：
- 节点亲和性/选择器配置缺失的具体文本未在输入中直接提供，但 Event (事实 #2) 明确指出失败原因是 **"didn't match Pod's node affinity/selector"**。
- 由于资源请求/限制 (事实 #3, #4) 均处于极低水平，且 K8s Event 明确排除了资源不足，因此调度失败的唯一确凿证据指向 **标签匹配失败**。
- Metrics (事实 #5) 进一步佐证了 Pod 处于持续未调度状态，未发生重启或进入其他异常状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 包含不存在的 nodeSelector/亲和性标签 → 集群 0/3 节点因标签不匹配被过滤 → FailedScheduling 事件触发 → Pod 持续 Pending 未分配 IP
```

### 根因结论

已确认的根因为：**调度器因 Pod 的节点选择器 (nodeSelector) 或亲和性 (affinity) 配置与集群现有节点标签不匹配，导致无法调度任何节点。**

- **证据支撑**：
  1. **直接失败机制**：事实 #2 (K8s Event) 明确指出 **"0/3 nodes are available: ... didn't match Pod's node affinity/selector"**，且该事件在 70 分钟内重复 13 次，排除了间歇性故障。
  2. **排除资源因素**：事实 #3 和 #4 显示 Pod 的资源请求/限制极低（5m CPU, 8Mi Memory），且 3 个节点均未因资源不足（Insufficient CPU/Memory）而被拒绝，进一步证实失败源于**标签/选择器匹配**。
  3. **状态一致性**：事实 #1 (K8s State) 和事实 #5 (Metric) 确认 Pod 在长达 70 分钟的时间内始终处于 Pending 状态，无任何调度进展。

- **补充说明**：
  虽然正式 RCA 中提到具体标签为 `aiops.lab/unavailable=true`，但输入事实中未提供该 Pod 配置的显式 JSON/YAML 片段作为证据（仅通过 Event 描述结果）。因此，根因确认为**“Pod 配置了与节点标签不匹配的选择器/亲和性规则”**，具体标签名称基于 Event 描述推导，但不影响“匹配失败”这一核心结论的确定性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 36.1s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 45.0s (Evidence 35.9s, RCA 9.0s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
