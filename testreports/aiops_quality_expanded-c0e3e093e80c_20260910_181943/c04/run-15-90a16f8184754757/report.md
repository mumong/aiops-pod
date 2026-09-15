## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 配置引用了 Secret 'aiops-case-04/workload-input' 中的 'unavailable-key'，但该 Secret 在集群中不存在或缺失该 key，导致 kubelet 无法完成容器配置。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (container: app) | 确证容器配置阶段失败，非运行期崩溃。 |
| 2 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 精确锁定缺失的资源标识符。 |
| 3 | K8s Event | kubernetes | `Warning Failed`: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (x12 over 27m) | 持续重复的失败事件，确证问题非瞬时网络抖动。 |
| 4 | K8s State | kubernetes | `pod.status`: `Pending`, `phase`: `Pending` | 确认 Pod 处于挂起状态，未进入调度后的运行阶段。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 | 遥测数据与 K8s 状态一致。 |

**证据印证说明：**
1.  **K8s 内部状态与遥测互证**：K8s 事件与等待信息直接指向 `Secret` 缺失，而 Prometheus 指标 `reason="CreateContainerConfigError"` 同步验证了该非正常状态。
2.  **缺失决定性事实**：由于 Pod 未启动（状态 `Pending`），Logging 与 Tracing 工具返回 `not_applicable`（物理上无法产生日志/Trace）。
3.  **未验证细节**：`collection` 中标记 `verify_secret_configmap` 等工具执行失败/无匹配，因此未直接观察到 Secret 对象本身，但报错信息已足以确立因果逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 中缺失 key 'unavailable-key' → Pod Spec 引用了该无效配置键 → Kubelet 解析配置时挂载失败 → 容器状态锁定为 CreateContainerConfigError
```

### 根因结论

**已确认根因：配置资源引用错误（Reference to Missing Secret Key）**

Pod `aiops-case-04/workload-6584f97c76-h4lt9` 在初始化配置阶段，尝试引用 Secret `aiops-case-04/workload-input` 中的键 `unavailable-key`，但该键不存在。这一配置错误导致 Kubelet 无法完成容器环境准备，从而产生 `CreateContainerConfigError` 状态并阻止 Pod 进入 Running 状态。证据（K8s State 报错、Event 日志、Waiting Reason 指标）在维度间高度一致，排除了网络或节点故障。

*注：虽然未能通过工具直接确认 Secret 对象是否存在（工具尝试未返回结果），但 Kubelet 的报错信息本身已构成确证性的失败机制证据，足以定位根因为配置定义与实际可用资源的冲突。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 36.7s (Evidence 29.5s, RCA 7.1s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
