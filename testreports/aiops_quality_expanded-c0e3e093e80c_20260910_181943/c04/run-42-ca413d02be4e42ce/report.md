## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器 app 启动失败，状态为 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: "CreateContainerConfigError"; `message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 直接指出容器配置错误及具体缺失的 Secret 键名 |
| 2 | K8s Event | kubernetes | `reason`: "Pulled"; `message`: "Container image... already present on machine" | 排除镜像拉取失败，确认为配置阶段阻塞 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1 | 量化确认等待原因分类 |
| 4 | K8s State | kubernetes | `pod.status`: "Pending"; `pod.condition` (Ready/ContainersReady): "False" | 确认 Pod 处于调度完成但容器未就绪的状态 |

**证据小结：**
K8s 状态直接报告了缺失 Secret 键的详细信息，Metric 从时序数据侧交叉验证了同一错误分类，事件日志排除了网络或镜像下载问题，证据链闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 缺少 'unavailable-key' 键值 → Pod 挂载请求该不存在的键 → kubelet 验证配置失败拒绝启动容器 → Pod 状态 Pending / 容器 CreateContainerConfigError
```

### 根因结论

**已确认的根因：** Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中的键 `unavailable-key`，但该键在 Secret 中不存在。

该配置错误导致 kubelet 在创建容器前验证阶段直接失败，表现为容器状态为 `CreateContainerConfigError`，Pod 保持 `Pending` [证据 1, 4]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.5s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 37.8s (Evidence 31.2s, RCA 6.4s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
