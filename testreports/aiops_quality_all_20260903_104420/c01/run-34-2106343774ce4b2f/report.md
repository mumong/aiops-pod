## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod 定义了节点选择器 `aiops.lab/unavailable=true`，但集群中全部 3 个节点均不包含该标签，导致调度器持续匹配失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: Pending (`fact-9f70cb27ff86`) | 确认 Pod 未启动的核心异常状态 |
| 2 | K8s Config | kubernetes | container.resource_request.memory: 8Mi (`fact-192ef819d61f`) | 排除资源请求不足导致的调度拒绝 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory: 32Mi (`fact-2985c47e99ca`) | 确认内存资源配额配置 |
| 4 | K8s Config | kubernetes | container.resource_request.cpu: 5m (`fact-38a32733d3e5`) | 排除资源请求不足导致的调度拒绝 |
| 5 | K8s Config | kubernetes | container.resource_limit.cpu: 50m (`fact-871963f5e87c`) | 确认 CPU 资源配额配置 |
| 6 | K8s Event | kubernetes | FailedScheduling: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" (`fact-0f2a9f8271d3`) | 确认 3 个节点因亲和性/选择器规则不匹配均无法调度 |
| 7 | K8s Event | kubernetes | FailedScheduling: Preemption: 0/3 nodes are available (`fact-3f8180960ec0`) | 确认抢占机制无效，问题在于节点标签缺失而非资源竞争 |
| 8 | Metric | prometheus | kube_pod_status_phase: Pending 为 1，Succeeded 为 0 (`fact-e7e64659b2f6`, `fact-5b7ae9124cb9`) | 侧面印证 Pod 持续处于 Pending 状态，未成功执行 |

**证据说明：**
1. **K8s Event** (`#6`, `#7`) 提供了直接的调度失败原因：3/3 节点均不符合选择器规则；**K8s Config** (`#2`-`#5`) 证实资源请求极低，排除资源瓶颈。
2. **Metric** (`#8`) 与 **K8s State** (`#1`) 一致确认了 Pod 长期处于 Pending 状态。
3. Logging/Tracing 因容器未启动或工具权限受限无法提供补充证据，但现有 K8s 事实链已闭合。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
节点选择器约束不匹配 #6, #7 → 调度器匹配失败 → 连续触发 FailedScheduling 事件 → Pod 保持 Pending 状态 #1
```

### 根因结论

**已确认的根因**：Pod 定义了节点选择器 `aiops.lab/unavailable=true`，但集群中全部 3 个节点均不包含该标签，导致调度器持续匹配失败 (`#6`)。

该根因直接导致 `default-scheduler` 拒绝将 Pod 调度到任何节点，进而引发 `Pending` 状态 (`#1`) 和持续 70 分钟内的 14 次 `FailedScheduling` 事件 (`#6`, `#7`)。资源请求配置 (`#2`-`#5`) 处于合理范围，确非根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.4s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 36.8s (Evidence 28.6s, RCA 8.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
