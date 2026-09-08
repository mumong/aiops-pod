## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 的 YAML 定义中引用了不存在于 Secret 'workload-input' 中的 key 'unavailable-key'。由于引用配置了 optional: false，kubelet 在解析环境变量时失败，直接导致容器进入 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `waiting_reason`: "CreateContainerConfigError" | 确证容器因配置问题处于等待状态 |
| 2 | K8s State | kubernetes | `waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 提供具体的配置缺失事实，定位根因 |
| 3 | K8s Event | kubernetes | `message`: "Normal Pulled 32s ... Container image ... already present" | 排除镜像拉取故障，确认镜像可用 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (labels: container: app, reason: CreateContainerConfigError) | 数值为 1，交叉印证 K8s 状态 |

K8s 状态与 Prometheus 指标（证据 1、2、4）在状态码和具体错误原因上完全一致，排除了镜像拉取问题（证据 3），确证故障源头在于配置引用。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'workload-input' 缺失 'unavailable-key' → optional: false 导致解析阻塞 → 容器创建失败 → CreateContainerConfigError
```

### 根因结论

已确认的根因是 **Secret 'workload-input' 中缺少被 Pod 引用且配置为 `optional: false` 的 key 'unavailable-key'**（证据 2、4）。

由于该环境变量配置未标记为可选，kubelet 无法获取所需的密钥值，导致容器初始化流程被阻断，从而引发 `CreateContainerConfigError` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.7s
├─ 并发证据采集: 82.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 82.7s (Evidence 74.7s, RCA 7.9s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
