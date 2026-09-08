## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 处于 Pending 状态，容器 app 报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: app 容器报错 `CreateContainerConfigError` ([fact-05537ec71235](fact-05537ec71235)) | 确认异常状态为配置挂载阶段失败 |
| 2 | K8s Event | Kubernetes | `Failed` 事件重复 12 次：`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` ([fact-d6f1850dbcb1](fact-d6f1850dbcb1), [fact-f57a4c518958](fact-f57a4c518958)) | 给出容器启动失败的直接原因与涉及资源 |
| 3 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` ([fact-f5cba7a26fba](fact-f5cba7a26fba)) | 事件信息的容器级状态复现 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 在 `reason=CreateContainerConfigError` 下值为 `1` ([fact-793a0d604ff7](fact-793a0d604ff7)) | 指标层面对配置错误状态的独立确认 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` 在 `phase=Pending` 下值为 `1`；`restarts_total=0` ([fact-9c7b017ebe3e](fact-9c7b017ebe3e), [fact-924fb4c12917](fact-924fb4c12917)) | 确认 Pod 处于未就绪等待状态且未发生重启 |

Kubernetes 事件与状态指标在 `CreateContainerConfigError` 上完全一致，证实该 Pod 当前仅因 Secret 键缺失导致无法挂载配置，未发生运行时计算或网络故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用 Secret 'aiops-case-04/workload-input' 中不存在的键 'unavailable-key' → kubelet 在挂载卷/环境变量时验证 Secret 失败 → 容器 'app' 无法启动并进入 Waiting(CreateContainerConfigError) → Pod 保持 Pending 且未发生重启
```

### 根因结论

已确认的根因为 Pod 规范中对 Secret `aiops-case-04/workload-input` 的键引用错误。Kubernetes 事件明确报告找不到键 `unavailable-key`，并伴随 `CreateContainerConfigError` 状态 ([fact-d6f1850dbcb1](fact-d6f1850dbcb1), [fact-f57a4c518958](fact-f57a4c518958), [fact-05537ec71235](fact-05537ec71235))。指标 `kube_pod_container_status_waiting_reason` 对该错误的独立观测 ([fact-793a0d604ff7](fact-793a0d604ff7)) 排除了瞬时网络或节点问题，进一步将故障点锁定在配置挂载校验失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.7s
├─ 并发证据采集: 55.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 55.8s (Evidence 48.2s, RCA 7.5s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
