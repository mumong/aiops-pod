## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认为 Secret 密钥缺失导致挂载失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` | 判定容器因配置错误处于等待状态 |
| 3 | K8s Event | kubernetes | `Warning  Failed  Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (x12 over 43m) | 提供高频重复的挂载失败事件，证明故障持续性 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` | 指标层独立确认了该特定等待原因 |
| 5 | K8s State | kubernetes | `pod.phase: Pending` / `ContainersReady: False` | 确认 Pod 调度成功但容器未就绪 |

**证据说明：**
*   K8s 原始状态、事件日志与 Prometheus 指标（事实 #1, #2, #3, #4）在错误类型（Secret Key 缺失）和状态（CreateContainerConfigError）上完全一致，形成多源交叉印证。
*   由于 Pod 处于启动前配置校验阶段（Waiting），日志与链路追踪工具查询失败且无业务日志产出（未纳入表格），不影响当前配置层面的根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 模板定义 SecretKeyRef 'unavailable-key' → Secret 'workload-input' 仅含 'available-key'，解析失败 → kubelet 挂载 Volume 报错 → Pod 持续处于 CreateContainerConfigError 状态
```

### 根因结论

已确认根因为 **Kubernetes Deployment 配置中引用了不存在的 Secret Key**。
*   Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器 `app` 尝试挂载 `Secret aiops-case-04/workload-input` 中的密钥 `unavailable-key`。
*   目标 Secret 实际数据不包含该 Key，导致 kubelet 在创建容器前校验失败（事实 #1, #2, #3）。
*   此问题由配置不当引起，与集群组件健康度或网络拓扑无关。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.4s
├─ 并发证据采集: 68.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 68.9s (Evidence 60.6s, RCA 8.1s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
