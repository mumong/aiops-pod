## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Missing NetworkAttachmentDefinition 'unavailable-network' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 状态：`Pending`；条件 `ContainersReady= False` (`ContainersNotReady`)；等待原因 `ContainerCreating` | 直接确认 Pod 处于调度完成但容器启动失败的阻塞状态 |
| 2 | K8s State | Kubernetes | `ContainerCreating` 诊断结论：缺少 NetworkAttachmentDefinition 'unavailable-network' | 揭示导致沙箱创建失败的直接约束条件 |
| 3 | K8s Event | Kubernetes | 容器 `app` 等待原因为 `ContainerCreating` | 与 K8s 状态一致，确认为非 CrashLoopBackOff 等非网络类错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值 `1`，标签 `reason="ContainerCreating"` (采样数：1) | 独立监控数据确认当前正有 1 个容器处于该等待状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值 `0` | 排除因 CrashLoopBackOff 或重启导致的重复现象，确认为首次或持续创建失败 |

**证据印证说明**
Kubernetes 状态（#1）与等待原因（#3）一致，均确认处于容器启动前的阻塞阶段。Prometheus 指标（#4）独立验证了该状态的实时性，且重启次数为 0（#5）排除了容器反复崩溃的可能。结合 K8s 配置中的诊断状态（#2），证据链闭合，指向网络附件定义缺失导致的沙箱创建失败。

## 🎯 根因分析 · g1

### 因果链

```text
Multus CNI 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → 网络插件查找 NAD 失败 (NoNetworkFound) → Pod 沙箱 (Sandbox) 创建失败 → Pod 持续处于 ContainerCreating 状态且处于 Pending 状态
```

### 根因结论

已确认根因为 **网络配置缺失 (Missing NetworkAttachmentDefinition)**。
集群中 Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的 Multus CNI 配置试图绑定至名为 `unavailable-network` 的网络附件定义，但该资源在集群中不存在。这导致 kubelet 在尝试创建 Pod 沙箱时网络初始化失败，容器无法进入运行状态。证据 `diagnosis` 字段已明确标识该缺失对象（证据 #2），且无其他竞争因子（如资源不足或节点故障，证据 #1 #5）佐证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 32.1s
├─ 并发证据采集: 48.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 48.2s (Evidence 43.0s, RCA 5.0s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
