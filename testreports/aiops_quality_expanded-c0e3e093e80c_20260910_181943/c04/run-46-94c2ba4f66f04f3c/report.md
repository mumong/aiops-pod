## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod Spec 中引用了 Secret aiops-case-04/workload-input，但该 Secret 中缺失 Pod 所需的环境变量键 'unavailable-key'。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 证实环境变量注入失败的具体机制 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `CreateContainerConfigError` | 确认 Pod 容器因配置问题未进入运行态 |
| 3 | K8s State | Kubernetes | `pod.phase`: `Pending` | 显示 Pod 停留在启动前的等待阶段 |
| 4 | K8s Event | Kubernetes | `event.message`: "Normal Pulled ... Container image ... already present on machine" | 排除镜像拉取失败的可能 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (label: `reason=CreateContainerConfigError`) | 指标层面证实了容器的等待原因与 K8s 状态一致 |

**证据印证说明：**
Kubernetes 状态指标直接捕获了 `CreateContainerConfigError`，且 `event` 中记录了镜像拉取成功的背景信息，排除了网络或存储类问题。`waiting_message` 提供了唯一的关键证据，精确锁定了配置依赖（Secret 中缺失特定 Key）这一根因。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺失环境变量键 'unavailable-key' → Pod 容器配置验证失败 (CreateContainerConfigError) → 容器无法启动且 Pod 停留在 Pending 阶段
```

### 根因结论

已确认根因为：**Pod Spec 引用的 Secret 中缺失了 Pod 所需的环境变量键 'unavailable-key'**。

依据证据 1（`container.waiting_message`）及证据 2、3、5（K8s 状态与 Metric），容器在配置阶段即被 Kubelet 拦截，导致 `CreateContainerConfigError` 且 `Pending`。证据链条闭合，无需进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 21.6s
├─ 并发证据采集: 555.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 555.9s (Evidence 551.9s, RCA 3.9s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
