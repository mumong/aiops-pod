## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 Pending 状态，容器 app 报错 CreateContainerConfigError，未能启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-05da339b65fa` | `container: "app", message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 直接根因事实，明确指出容器启动失败的具体缺失对象 |
| 2 | K8s State | `fact-e916b0fb9bd7` | `container: "app", reason: "CreateContainerConfigError"` | 确证 K8s 层面的容器创建阻塞原因与失败类型 |
| 3 | K8s State | `fact-0f44772a13e4` | `status: "Pending"` | 描述 Pod 当前的宏观停滞状态，佐证未能进入 Running |
| 4 | K8s Event | `fact-53def5fad4fd` | `type: "Warning", reason: "Failed", message: "Warning  Failed          8m2s (x12 over 9m59s)   kubelet            Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 聚合事件展示该错误已持续约 10 分钟，且 kubelet 已重试失败多次 |
| 5 | Metric | `fact-4d65a6b96b48` | `attribute: kube_pod_container_status_waiting_reason, value: 1 (reason: CreateContainerConfigError)` | 独立监控指标再次印证容器正等待且原因确认为配置错误 |
| 6 | K8s State | `fact-16c79affc51e` | `container: "app", restart_count: 0` | 排除重启风暴（CrashLoopBackOff）可能，确证处于创建前置阶段 |

**证据说明：**
- 证据 1、2、4 共同指向同一个确定性错误：Secret `aiops-case-04/workload-input` 中缺失 key `unavailable-key`，导致 Kubelet 拒绝创建容器。
- 证据 3、5、6 分别从 Pod 阶段（Pending）、监控指标（waiting_reason=1）和重启计数（0）确认了现象的持续性，排除了运行时内存/资源限制（如 OOM）导致的应用内部崩溃可能。
- Metric 与 K8s 事实高度一致，相互印证根因结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret `workload-input` 中不存在的 key `unavailable-key` → Kubelet 创建容器配置校验失败 → 容器初始化阶段被阻断（CreateContainerConfigError） → Pod 持续处于 Pending 状态且无应用日志产生
```

### 根因结论

**已确认根因：** Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器 `app` 配置了引用 Secret `aiops-case-04/workload-input` 中名为 `unavailable-key` 的 key。Kubelet 在启动容器时查找该 key 失败（`couldn't find key unavailable-key`），从而抛出 `CreateContainerConfigError` 并阻止容器启动。
- 证据编号：1, 2, 3, 4

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 13.2s
├─ 并发证据采集: 57.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 57.0s (Evidence 47.9s, RCA 8.9s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
