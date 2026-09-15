## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 Pending 状态，容器 app 处于 CreateContainerConfigError，未能启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `container.app` waiting reason: `CreateContainerConfigError` | 标识容器启动失败的确切原因类型。 |
| 2 | K8s State | kubernetes | 等待消息: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供导致配置加载失败的具体缺失资源名与键名。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 | 独立确认了等待状态的原因与 K8s API 观测结果一致。 |
| 4 | K8s Config | kubernetes | 资源请求 `cpu=5m, memory=8Mi`；硬限制 `cpu=50m, memory=32Mi` | 排除因资源配额（CPU/内存）不足导致的调度或启动失败。 |

**证据说明：**
1. K8s API 返回的 `CreateContainerConfigError` 与 Prometheus 指标的等待原因标签 `reason="CreateContainerConfigError"` 相互印证，确认了故障现象在控制平面和监控层面的一致性。
2. K8s 事件中的具体报错消息直接定位了配置失败的根源，即挂载卷时解析 Secret 引用失败，该事实足以解释容器未能进入 `Running` 或 `CrashLoopBackOff` 状态，因为启动前的配置挂载阶段即已中断。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺失 key 'unavailable-key' → kubelet 挂载 Volume 解析 Secret 失败 → 容器 'app' 初始化失败，状态转为 CreateContainerConfigError → Pod 保持在 Pending 阶段，容器未启动
```

### 根因结论

**已确认的根因：** Pod 规范（Spec）中引用了 `aiops-case-04/workload-input` Secret 中的 `unavailable-key`，但该键在 Secret 中不存在（或未被挂载），导致 kubelet 无法完成容器配置阶段的挂载操作。

**引用证据：**
*   证据 #2 中的真实原始结果直接显示了 Kubernetes API 返回的失败原因。
*   证据 #1 和 #3 确认了此错误状态已被持久化和监控。

**关于未知项：**
*   为何 Secret 中缺少该键（如配置变更丢失或创建错误）目前缺乏配置审计日志支持，属于“未确认”项，但不影响当前故障现象的直接解释。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.2s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 39.4s (Evidence 30.0s, RCA 9.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
