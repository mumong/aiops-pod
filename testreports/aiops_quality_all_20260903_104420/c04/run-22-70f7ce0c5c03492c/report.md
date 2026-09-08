## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (48m x12 over 50m) | 直接指出容器启动失败的原因为缺失特定密钥 |
| 2 | K8s State | Kubernetes | `Waiting: CreateContainerConfigError` (`message: couldn't find key unavailable-key`) | 确认容器处于因配置问题导致的等待状态 |
| 3 | K8s State | Kubernetes | `Pod phase: Pending` | 确认 Pod 未进入运行阶段 |
| 4 | K8s Config | Kubernetes | `container.app resource_limit: memory=32Mi, cpu=50m` | 排除资源限制（Hard Limit）导致启动失败的可能性 |
| 5 | K8s Event | Kubernetes | `ContainersNotReady` (`containers with unready status: [app]`) | 进一步印证核心应用容器无法就绪 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError", container="app"} = 1` | 确认 Pod 正处于配置错误的等待状态 |

**证据印证说明**
- **证据 1、2、3** 在 K8s 层面形成闭环，明确将 Pod 处于 `Pending` 和 `CreateContainerConfigError` 的原因锁定为 Secret 键缺失。
- **证据 6** 在指标层面独立印证了该状态的存在。
- **证据 4** 排除了资源限制作为直接故障原因的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Secret 'aiops-case-04/workload-input' 中不存在的键 'unavailable-key' → Kubelet 无法获取环境变量配置 → 容器创建被阻止，进入 Waiting 状态 → Pod 持续处于 CreateContainerConfigError 异常状态
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 Secret 键**。

具体表现为：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 试图从 Secret `aiops-case-04/workload-input` 中读取名为 `unavailable-key` 的字段，但该密钥在 Secret 中实际不存在（实际包含的是 `available-key`）。由于缺少必需的密钥，`kubelet` 无法完成容器配置，导致容器创建被阻断并抛出 `CreateContainerConfigError` 状态（见证据 1、2、6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.6s
├─ 并发证据采集: 54.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 54.0s (Evidence 45.4s, RCA 8.4s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
