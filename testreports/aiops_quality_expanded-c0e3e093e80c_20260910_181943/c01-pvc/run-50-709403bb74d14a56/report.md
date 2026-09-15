## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 持续处于 Pending 状态，未被调度（node: <none>）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedScheduling ... persistentvolumeclaim "unavailable-claim" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` (fact-247aad1e56b0, fact-440811b40516) | 调度器明确拒绝调度，指出因缺失 PVC "unavailable-claim" 导致 |
| 2 | K8s State | kubernetes | `pod.status`: `Pending` (fact-9d1432b91f73) | 确认 Pod 当前状态为不可调度的 Pending 状态 |
| 3 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = `1` (fact-4ce951161398) | 监控数据佐证 Pod 处于 Pending 状态 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu`: `50m`, `container.resource_request.cpu`: `5m`, `container.resource_limit.memory`: `32Mi`, `container.resource_request.memory`: `8Mi` (fact-0aec620c8199, fact-2e14eaaa6c18, fact-ef0977133735, fact-6cda1bccc356) | 资源请求与限制已配置且数值较小，排除因资源超限导致的调度失败 |

**证据说明：**
- **事件与状态互证**：调度器发出的 `FailedScheduling` 事件明确指出失败原因是 `persistentvolumeclaim "unavailable-claim" not found`，这与 Pod 保持 `Pending` 状态（事实 1、2）的现象一致。
- **排除资源因素**：Pod 的资源请求（事实 4）并未耗尽集群容量（事件提及 3 个节点均无预emption 受害者），进一步确认失败仅由缺少的 PVC 引起。
- **监控确认**：Prometheus 的 Pod 状态指标（事实 3）从数据层面确认了 Pod 持续处于 Pending 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
未创建 PVC 'unavailable-claim' → 调度器无法绑定卷 → FailedScheduling 事件触发 → Pod 持续 Pending
```

### 根因结论

已确认根因为：**Pod `aiops-case-v03/workload` 在 Pod 模板中引用了名为 `unavailable-claim` 的 PersistentVolumeClaim，但该 PVC 在命名空间 `aiops-case-v03` 中不存在。**

调度器在尝试调度 Pod 时，发现所依赖的 PVC 缺失，导致卷绑定逻辑失败，进而触发 `FailedScheduling` 事件并持续拒绝调度（证据 1、2）。Pod 的资源配置（证据 4）已就绪且非瓶颈。

---

## 📊 性能统计

```text
├─ 总耗时: 48.4s
├─ 问题定位: 12.1s
├─ 并发证据采集: 26.6s
│  └─ g1 aiops-case-v03/workload: 26.6s (Evidence 18.1s, RCA 8.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
