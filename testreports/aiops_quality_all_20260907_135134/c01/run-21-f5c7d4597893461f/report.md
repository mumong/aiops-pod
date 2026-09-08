## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 定义了 nodeSelector 'aiops.lab/unavailable=true'，但集群中所有节点均未设置该标签，导致调度器因亲和性/选择器不匹配而无法分配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (发生 38m 及持续 33m) | 确认集群节点无法匹配 Pod 调度要求 |
| 2 | K8s State | `Pod condition` | `PodScheduled=False`，原因 `Unschedulable`，信息同上 | 确认 Pod 当前处于调度失败状态 |
| 3 | K8s State | `Pod status` | `status: Pending`, `phase: Pending` | 确认 Pod 尚未进入运行阶段 |
| 4 | K8s Config | `Resource Request` | Container `app`：CPU `5m`, Memory `8Mi` | 确认资源申请极小，排除因资源不足导致调度失败 |
| 5 | Metric | `prometheus` | `kube_pod_status_phase{phase="Pending"}=1`；`phase="Succeeded"=0` | 确认 Pod 状态在监控侧一致显示为等待/未运行 |

**证据分析：**
证据 1 与证据 2 互证，明确指出失败机制是 `node affinity/selector` 不匹配。证据 3 与证据 5 确认了 Pod 的长期阻塞状态。证据 4 证明集群不存在因资源短缺导致的竞争，从而将根因锁定在节点选择器配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector 'aiops.lab/unavailable=true' 而集群节点无此标签 → 调度器无法分配节点 → Pod 状态 Pending → 用户侧 Pod 运行阻塞
```

### 根因结论

**已确认根因：** Pod 的调度配置错误。
该 Pod 定义了 `nodeSelector 'aiops.lab/unavailable=true'`，但集群中所有可用节点均未设置该标签。调度器因此判定 0/3 个节点可用，导致 Pod 持续处于 `Pending` 状态 [证据 #1, #2]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 30.6s
├─ 并发证据采集: 37.0s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 37.0s (Evidence 30.3s, RCA 6.6s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
