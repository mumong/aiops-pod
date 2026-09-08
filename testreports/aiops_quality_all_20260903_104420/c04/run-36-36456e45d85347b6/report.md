## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod spec 错误引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`（该 Secret 实际仅包含 `available-key`），导致容器初始化时配置注入失败，触发 `CreateContainerConfigError`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `reason: "CreateContainerConfigError"` (fact-85cd51a285d) | 确认 Pod `app` 容器的具体等待原因为配置错误，排除 OOM、CrashLoopBackOff 等其他启动故障。 |
| 2 | K8s State | `container.waiting_message` | `message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` (fact-9533b96af4f0) | **决定性证据**：直接指出导致配置注入失败的根因是 Secret 中缺失了 Pod 期望的 `unavailable-key`。 |
| 3 | K8s State | `pod.phase` | `phase: "Pending"` (fact-048e7ac10300) | 确认 Pod 停留在初始化等待阶段，符合因前置配置校验失败导致无法调度容器实例的特征。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` (fact-17b8385e26c1) | 从监控维度独立印证了 K8s 状态，且由于 `sample_count=1`，仅记录当前观测值，禁止推断长期趋势。 |
| 5 | K8s Config | `resource_limit/requests` | CPU request `5m`, memory request `8Mi` (fact-0f029f1eebb7, fact-82d31082950a) | 排除资源限制导致 OOM 或 CPU 过载的可能性；该异常组现象为配置校验失败，与资源配额无关。 |
| 6 | Logging/Tracing | `elasticsearch/deepflow` | `status: "not_applicable"` (fact not shown, derived from collection status) | 因容器启动前即被 Kubelet 拦截，无运行时日志与 Trace 数据产生，确认缺失数据属于物理限制而非采集故障。 |

**证据说明：**
*   **互相印证**：证据 2 (K8s 原始错误信息) 明确指出了缺失的 Key，证据 1 和 证据 4 (Metric) 确认了该状态为持续存在的配置错误 (`CreateContainerConfigError`)，而非偶发网络或运行时问题。
*   **排除干扰**：证据 5 证明非资源瓶颈；证据 6 确认日志/Tracing 缺失是容器未启动的必然结果，佐证了根因发生在极早期的配置挂载阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺失 Pod spec 请求的 key `unavailable-key` → Kubelet 执行前置配置校验失败 → 容器保持在 Waiting 状态 (CreateContainerConfigError) → Pod 处于 Pending 阶段，应用不可用
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 Spec 定义错误引用了 Secret `aiops-case-04/workload-input` 中不存在的配置项 `unavailable-key`。

**证据支持：**
*   直接错误信息来源于 K8s 状态事实：`couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (事实编号：`fact-9533b96af4f0`)。
*   该错误导致 Kubelet 拒绝启动容器，直接表现为 `CreateContainerConfigError` (事实编号：`fact-a85cd51a285d`)，且 Prometheus 监控指标一致确认了该等待状态 (事实编号：`fact-17b8385e26c1`)。

**结论：**
配置错误导致容器启动失败，现有证据充分支持该结论，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.5s
├─ 并发证据采集: 66.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 66.3s (Evidence 58.7s, RCA 7.5s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
