## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 状态为 Pending，容器 `app` 报错 `CreateContainerConfigError`，无法创建 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-b144a1394e22` | `container.waiting_reason`: `CreateContainerConfigError` (container: `app`) | 明确直接失败机制 |
| 2 | K8s State | `fact-b2dc85fb8aaa` | `container.waiting_message`: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (container: `app`) | 指向具体缺失配置项 |
| 3 | K8s Event | `fact-3c2d53af8fbe` | `kubelet` 报错: `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (x12 over 39m) | 确认 Kubelet 在挂载阶段因缺失 key 持续失败 |
| 4 | K8s State | `fact-2d8a1ad8c682` | `pod.status`: `Pending` | 确认 Pod 无法进入 Running 阶段 |
| 5 | Metric | `fact-6e07dc07abe5` | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"}`: `1` | 验证异常状态的持续性 |

上述 Kubernetes 事件与状态事实一致确认：`app` 容器因 Kubelet 无法在 ConfigMap `workload-input` 中找到名为 `unavailable-key` 的 Key 而进入 `CreateContainerConfigError` 状态，导致 Pod 卡在 `Pending`。Metric 数据印证了该异常状态在当前时刻依然存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了 ConfigMap `workload-input` 中的 Key `unavailable-key` → ConfigMap 实际缺少该 Key (可能仅含 `available-key`) → Kubelet 挂载配置失败 → Pod 状态 Pending，容器报错 CreateContainerConfigError
```

### 根因结论

已确认根因为：Pod 定义错误引用了 ConfigMap `workload-input` 中不存在的 Key `unavailable-key`。

**证据支持**：
- 容器 `app` 的直接失败原因为 `CreateContainerConfigError` (`fact-b144a1394e22`, `fact-6e07dc07abe5`)。
- 失败的具体消息明确指出 `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (`fact-b2dc85fb8aaa`, `fact-3c2d53af8fbe`)。
- 该错误由 Kubelet 在挂载配置阶段捕获并持续报告 (`fact-3c2d53af8fbe`)。

**未确认项**：
- 部署配置为何引用不存在的 Key（是配置错误或资源未更新）。
- 其他容器或 Sidecar 是否受相同影响。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 13.2s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-v11/workload: 48.5s (Evidence 39.9s, RCA 8.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
