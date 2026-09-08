## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 的容器配置（YAML）引用了 Secret aiops-case-04/workload-input 中的 key 'unavailable-key'，但实际 Secret 对象中仅包含 key 'available-key'，导致 kubelet 在创建容器时因找不到指定 key 而触发 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CreateContainerConfigError | 核心诊断证据，锁定容器启动前的配置检查失败阶段 |
| 2 | K8s State | kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 精确指向故障实体：Secret `aiops-case-04/workload-input` 中缺失名为 `unavailable-key` 的 key |
| 3 | K8s Event | kubernetes | `Warning Failed`: "Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 事件日志重复佐证（x12 over 61m），确认为持续且未自愈的异常 |
| 4 | K8s Config | kubernetes | `resource_limit.cpu`: 50m, `resource_limit.memory`: 32Mi | 排除资源限制导致 Pod 启动失败的可能（配置仅为背景参考） |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=1 (`reason=CreateContainerConfigError`) | Metric 状态与 K8s 状态一致，独立确认容器持续处于等待配置错误状态 |

**证据印证：**
Kubernetes 状态 (`#1`, `#2`) 与事件 (`#3`) 均明确指向 Secret 挂载配置中的 key 缺失问题，且 Metric (`#5`) 独立验证了该状态持续存在。容器重启次数为 0 (`fact-256809ec1d0f`) 且未产生日志 (`Logging.status=not_applicable`)，进一步佐证故障发生在容器启动之前的 kubelet 配置校验阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 引用不存在的 Secret key ('unavailable-key') → kubelet 验证 Secret 挂载配置失败 → 容器启动流程中止 (CreateContainerConfigError) → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置错误地引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`（实际 Secret 中仅包含 `available-key`）。这一配置错误导致 kubelet 在尝试挂载卷时找不到指定 key，从而抛出 `CreateContainerConfigError` 并中止容器创建过程。

**证据支持：**
- Kubernetes 状态明确指出 `container.waiting_reason` 为 `CreateContainerConfigError` 且 `waiting_message` 显示找不到 `unavailable-key` (`#1`, `#2`)。
- Metric `kube_pod_container_status_waiting_reason` 同样报告了 `CreateContainerConfigError` (`#5`)。
- 异常组诊断状态为 `diagnosed`，且正式 RCA 已通过配置验证（`diagnosis_publishable: true`）。

**缺失的决定性事实：**
无。当前 Kubernetes 状态、事件和 Metric 已构成完整证据链，足以确认配置引用错误为根本原因。Logging 和 Tracing 的缺失是因容器未启动导致，不影响根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 14.4s
├─ 并发证据采集: 60.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 60.7s (Evidence 52.3s, RCA 8.2s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- 未调用 Runbook
