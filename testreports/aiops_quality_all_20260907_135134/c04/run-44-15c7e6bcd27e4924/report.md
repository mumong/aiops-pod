## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，app 容器报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet | `container.waiting_reason="CreateContainerConfigError"` (Container: app) | 确立容器启动失败的直接状态 |
| 2 | K8s Event | kubelet | `message="couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 提供配置失败的具体键名缺失证据 |
| 3 | K8s State | kubelet | `pod.phase="Pending"`, `pod.condition.Ready.status="False"` | 确认 Pod 因配置问题无法进入运行态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason="CreateContainerConfigError", container="app") | 独立观测验证 K8s 状态中的等待原因 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (container="app") | 证实故障持续存在，容器未尝试过重启 |
| 6 | K8s Config | kubelet | 资源配置上下文: cpu_limit="50m", memory_request="8Mi", memory_limit="32Mi" | 排除资源不足（CPU/Memory）导致调度或启动失败的可能 |

**证据关联说明**：
1. K8s Event（#2）直接解释了 K8s State（#1）中 `CreateContainerConfigError` 的成因：Secret 密钥缺失。
2. Metric 数据（#4）在独立维度上验证了同一异常状态；Metric（#5）与 K8s 重启计数（#6 隐含在 K8s State 上下文）一致，表明该配置错误是持续性的，而非瞬时网络问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 Secret 键 → Secret 键查找失败机制 → 容器创建失败 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

根因已确认：Pod 容器配置（`app` 容器）请求从 Secret `aiops-case-04/workload-input` 中提取键名为 `'unavailable-key'` 的键，但该 Secret 中实际不存在此键（仅包含其他键）。这导致 `kubelet` 在拉取镜像后，因无法注入必要的配置/环境变量，直接以 `CreateContainerConfigError` 状态终止容器创建，使 Pod 维持在 `Pending` 状态。

**关键证据**：
- **fact-2a3f67896093** (K8s State): 确认 Pod 处于 `Pending` 状态。
- **fact-0710b554de48** (K8s Event): 明确指出错误原因是 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`。
- **fact-ea301d2d98bc** (Metric): `kube_pod_container_status_waiting_reason` 值为 1，reason 为 `CreateContainerConfigError`。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 20.3s
├─ 并发证据采集: 111.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 111.6s (Evidence 104.3s, RCA 7.1s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error, pod-imagepull-failed, pod-oomkilled
