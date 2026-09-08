## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 配置引用了 Secret 'aiops-case-04/workload-input' 中的 key 'unavailable-key'，但该 key 在 Secret 中不存在，导致容器启动失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: app -> CreateContainerConfigError | 直接定位到容器启动阶段的配置挂载错误 |
| 2 | K8s State | kubernetes | container.waiting_message: app -> "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 确切的错误信息指向缺失的 Secret Key |
| 3 | K8s Event | kubernetes | kubelet 54s (x347 over 75m) Container image "xnet.registry.io:8443/observability/python:3-alpine" already present | 证明镜像拉取成功，排除网络或镜像源问题 |
| 4 | K8s State | kubernetes | pod.condition: Ready=False, reason=ContainersNotReady | 确认 Pod 处于不可用状态，等待容器就绪 |
| 5 | K8s State | kubernetes | pod.phase: Pending | 确认 Pod 未进入 Running 状态 |
| 6 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1, labels={container: "app", reason: "CreateContainerConfigError"} | 独立时序数据验证了 K8s 状态中的错误类型 |
| 7 | Metric | prometheus | kube_pod_status_phase: 1, labels={phase: "Pending"} | 独立时序数据验证了 Pod 处于 Pending 状态 |
| 8 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 确认容器从未成功启动，排除了运行期崩溃重启的可能 |

**证据说明：**
1. **K8s 状态与事件互相印证**：Fact 1-2 显示 Kubelet 在尝试启动容器时，因找不到指定 Secret Key 而报错 `CreateContainerConfigError`；Fact 3 证明镜像拉取是正常的，排除了底层基础设施问题。
2. **时序数据与 K8s 状态一致**：Fact 6-7 从 Prometheus 角度独立确认了容器处于等待状态且原因为配置错误，Pod 处于 Pending 阶段。
3. **排他性证据**：Fact 8 的重启计数为 0，结合 Fact 2 的配置错误信息，确认故障发生在容器启动前的挂载阶段，而非启动后的应用崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 中缺少 key 'unavailable-key' → Kubelet 挂载失败 → 容器配置初始化错误 (CreateContainerConfigError) → Pod 处于 Pending 状态且未启动
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置中引用了 Secret `aiops-case-04/workload-input` 中的 `unavailable-key`，但该 Secret 中实际不存在此 key。这导致 Kubelet 在尝试挂载 Secret 数据到容器时失败，进而引发了 `CreateContainerConfigError`，使得容器无法完成启动，Pod 持续保持在 Pending 状态。

**证据引用：**
- K8s 报错明确指出无法找到该 key（Fact 2, 4, 5）。
- 时序数据独立验证了该错误类型和 Pending 状态（Fact 6, 7）。
- 容器从未重启，确认为启动阶段故障（Fact 8）。

**未确认因素：**
- Secret `aiops-case-04/workload-input` 中实际存在的 key 列表。
- `unavailable-key` 的缺失是源于初始配置错误，还是该 Secret 在后续运维中被误删或更新。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 42.7s (Evidence 35.9s, RCA 6.7s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
