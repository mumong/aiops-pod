## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 Pending/Waiting 状态，容器无法启动，持续报 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: Pending; ContainersReady: False (reason: ContainersNotReady) | 确认容器因配置问题处于未就绪状态，未启动成功 |
| 2 | K8s State | kubernetes | Container waiting reason: `CreateContainerConfigError`; message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指出容器配置错误是由特定 Secret 缺失 key 引起的 |
| 3 | K8s Event | kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供了 kubelet 拒绝启动容器的直接日志证据，指向配置引用异常 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=CreateContainerConfigError): 1 | 验证了容器确实停滞在配置错误阶段，与 K8s 状态一致 |

**证据关联说明：**
Metric 数据验证了 K8s 状态，证实容器确实处于 `CreateContainerConfigError` 状态（#1、#4）。关键的错误原因直接由 Container waiting message 和 Kubelet 事件明确给出：在 Secret `aiops-case-04/workload-input` 中寻找 key `unavailable-key` 失败（#2、#3）。两者共同构成了完整的事实链条。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义引用了 Secret 'aiops-case-04/workload-input' 中的 key 'unavailable-key' → Secret 中不存在该 key → kubelet 注入环境变量失败 (CreateContainerConfigError) → 容器状态停滞在 Pending/Waiting，无法启动
```

### 根因结论
已确认的根因是 Pod 配置引用了不存在的 Secret Key。具体证据如下：
1. K8s 容器等待状态 `CreateContainerConfigError` 直接指出配置缺失 (#2)。
2. Kubelet 事件日志 `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` 提供了精确的错误细节 (#3)。
3. Prometheus 指标确认了该错误状态的持续性 (#4)。

无需补充其他日志或追踪信息，现有 Kubernetes 事实已充分且唯一地解释了容器无法启动的原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.3s
├─ 并发证据采集: 41.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 41.0s (Evidence 32.3s, RCA 8.5s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
