## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的容器配置中引用了 ConfigMap aiops-case-v11/workload-input 中不存在的 key 'unavailable-key'，导致 kubelet 在启动容器时校验失败，触发 CreateContainerConfigError 并使 Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Event Failed: Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (12次, 24m-26m) | 直接证据：kubelet 明确指出因 ConfigMap 缺少 key 而校验失败 |
| 2 | K8s State | kubernetes | `pod.status: Pending` (fact-50a7b0ffc17f) | 现象：Pod 因容器创建失败而停滞在启动前状态 |
| 3 | K8s Event | kubernetes | Pod 网络状态：`cni.projectcalico.org/podIP: 172.16.104.60/32` (fact-3c631905b3c1) | 排除 CNI 网络故障，Pod 网络分配正常，问题限定在容器运行时/配置层 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=CreateContainerConfigError, value=1) | 指标印证：Prometheus 侧状态与 K8s Event 中的错误原因完全一致 |

**证据总结：**
K8s 事件明确指出了具体的配置错误（找不到 ConfigMap 的 key），Metric 状态进一步确认了该错误导致的容器状态。由于容器从未成功启动，Logging 和 Tracing 为空（事实层面预期结果），证据链仅依赖 K8s 状态与事件即可完成判定。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 ConfigMap key 'unavailable-key' → kubelet 校验容器配置失败 → 容器状态卡住 Waiting (CreateContainerConfigError) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 配置错误**：Pod `aiops-case-v11/workload` 在其容器配置中引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 Key `'unavailable-key'` [1]。

这一错误导致 `kubelet` 在创建容器前无法完成配置解析，进而触发了 `CreateContainerConfigError`。该机制直接表现为容器启动失败，使 Pod 无法从 `Pending` 状态进入 `Running` 状态 [2][3]。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 18.2s
├─ 并发证据采集: 556.8s
│  └─ g1 aiops-case-v11/workload: 556.8s (Evidence 548.3s, RCA 8.4s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
