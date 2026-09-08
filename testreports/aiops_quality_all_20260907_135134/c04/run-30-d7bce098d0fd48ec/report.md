## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod spec 中引用了 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key'，导致 kubelet 无法创建容器配置。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input (40m x12 over 42m) | **确证性证据**：明确指向 Secret 配置错误，解释了容器无法启动的直接原因 |
| 2 | K8s Event | kubernetes | podIP: 172.16.104.61/32; podIPs: 172.16.104.61/32; containerID: 8de036ca264878abe5f9be084b92ff3738423c5ea447a6d637ca78afda900174 | **上下文证据**：说明 Pod 已申请到网络资源，CNI 注入成功，问题不发生在网络插件层 |
| 3 | K8s State | kubernetes | Pending | **症状**：与 Event 记录一致，Pod 处于挂起状态无法创建容器 |
| 4 | K8s Config | kubernetes | resource_limit.memory: 32Mi; resource_request.cpu: 5m; resource_limit.cpu: 50m; resource_request.memory: 8Mi | **上下文证据**：资源配额设置正常，非资源耗尽导致的故障 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1 (label: reason=CreateContainerConfigError) (sample_count: 1) | **症状确认**：确认等待原因为配置类错误 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 (sample_count: 1) | **排他性证据**：重启次数为 0，排除启动后崩溃反复重启的可能 |
| 7 | Metric | prometheus | kube_pod_status_phase: 0 (label: phase=Running), 1 (label: phase=Pending) | **状态同步**：确认 Pod 整体处于 Pending 阶段 |

**证据互证说明：**
Kubernetes 事件（#1）明确指出了 `CreateContainerConfigError` 的根因为 Secret key 缺失，这与 Metric（#5）中的 `CreateContainerConfigError` 等待原因、以及 Pod 状态（#3）完全一致。K8s 事件中的网络分配记录（#2）排除了底层网络组件的问题，而 Metric 显示重启次数为零（#6）进一步确认了故障处于启动前的配置校验阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 中引用了 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key' 
→ kubelet 校验 Secret 失败 
→ 无法创建容器配置 (CreateContainerConfigError) 
→ Pod 保持在 Pending 状态且无法运行
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 在 Spec 中配置了环境变量或挂载卷引用了 Secret `aiops-case-04/workload-input` 的 key `unavailable-key`，但该 key 在实际 Secret 中不存在。
证据编号 #1（K8s Event）直接捕获了 kubelet 报错 `couldn't find key unavailable-key`，确证了配置错误。证据编号 #5（Metric）与 #3（K8s State）共同印证了该故障直接导致了 Pod 处于 `CreateContainerConfigError` 的 Pending 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.6s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 36.6s (Evidence 30.5s, RCA 6.0s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- 未调用 Runbook
