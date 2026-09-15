## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器 app 持续处于 Waiting (CreateContainerConfigError)，Pod 未运行且无重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接证实环境变量提取失败，指出缺失的 Secret 键名 |
| 2 | K8s State | Kubernetes | Pod 状态: `Pending`; 容器重启次数: `0` | 证实 Pod 处于无法运行的初始阻塞状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = `1` (采样数=1) | 量化确认容器因配置错误处于 Waiting 状态，未进入运行 |
| 4 | K8s Config | Kubernetes | 资源请求: CPU `5m`, 内存 `8Mi`；资源限制: CPU `50m`, 内存 `32Mi` | 排除资源配额导致的调度失败或 OOM |

上述证据形成闭环：Metric 确认了“配置错误”的等待状态，Kubernetes 事件明确指出了是特定的 Secret 键（`unavailable-key`）不存在导致无法提取环境变量，资源配置事实排除了其他资源相关的启动故障。

## 🎯 根因分析 · g1

### 因果链
```text
Secret 'aiops-case-04/workload-input' 中缺少键 'unavailable-key' → 
kubelet 在容器启动阶段无法提取 Pod 定义的指定环境变量 → 
容器启动失败，状态转为 Waiting (CreateContainerConfigError) → 
Pod 保持 Pending 状态，应用无法运行
```

### 根因结论
已确认的根因为 **Pod 配置引用的 Secret 中存在缺失字段**。
具体而言，Pod `aiops-case-04/workload-6584f97c76-h4lt9` 中定义的环境变量挂载指向了 Secret `workload-input`，要求包含键 `unavailable-key`，但该 Secret 实际不包含此键（证据 #1）。这直接导致了 `CreateContainerConfigError`（证据 #3）和 Pod 的 `Pending` 状态（证据 #2），且因配置问题无法自行恢复，容器未发生重启（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.5s
├─ 并发证据采集: 76.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 76.1s (Evidence 67.7s, RCA 8.3s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
