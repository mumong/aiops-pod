## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 Pending 状态且容器处于 CreateContainerConfigError 失败状态，未恢复。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed 26m (x12 over 28m) kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-625d2c7c89f2) | 确认 kubelet 因 Secret 键缺失导致挂载/注入失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason="CreateContainerConfigError"`, `container.waiting_message="couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` (fact-700e5d7f8ae1, fact-c6d651c556ca) | 标识容器处于配置错误的等待状态 |
| 3 | K8s State | kubernetes | `pod.phase="Pending"`, `ContainersReady=False`, `Ready=False` (fact-261ec71953bc, fact-1ce97e7ce211, fact-9ab266afa504) | 确认 Pod 因容器不可用而持续处于 Pending 阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` (fact-a2d0239f8587) | 从监控侧独立观测到 CreateContainerConfigError 状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` (fact-356b4b92ce9d) | 确认容器从未启动过，排除重启循环导致 |

**证据印证说明：**
K8s Event (1) 直接指出了具体的失败原因（Secret 中缺少 'unavailable-key'），与 Container State (2) 的等待信息完全一致。Metrics (4, 5) 从外部视角验证了容器长期处于配置错误状态且无重启历史，印证了该配置错误导致容器无法启动的持续性现象。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 缺少 key 'unavailable-key' → Pod spec 引用该不存在 key 导致容器配置校验失败 → Kubelet 报错并拒绝创建容器 → 容器进入 CreateContainerConfigError 状态，Pod 持续 Pending
```

### 根因结论

已确认根因为 Pod 的 YAML 配置中引用了不存在的 Secret 键。
1. **直接证据**：Kubelet 事件明确指出在 Secret `aiops-case-04/workload-input` 中找不到键 `unavailable-key` (证据1, 2)。
2. **状态确认**：容器因配置错误（`CreateContainerConfigError`）无法启动，且从未发生过重启 (证据2, 5)，符合引用无效资源导致启动失败的预期行为。
3. **现象对应**：上述机制直接导致 Pod 无法完成初始化并进入 Ready 状态 (证据3, 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.1s
├─ 并发证据采集: 44.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 44.1s (Evidence 34.6s, RCA 9.4s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
