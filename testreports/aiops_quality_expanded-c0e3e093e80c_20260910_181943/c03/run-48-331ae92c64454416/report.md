## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 卡在 ContainerCreating/Pending 状态，无法启动应用容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-861a8a170706, fact-d556c14e8f2e) | Warning FailedMount: kubelet 报告 "timed out waiting for the condition" 及 "MountVolume.SetUp failed for volume \"input\" : configmap \"unavailable-config\" not found" | 直接证明挂载卷失败的根本原因是配置缺失 |
| 2 | K8s State | kubernetes (fact-65594218e962) | container.waiting_reason: ContainerCreating | 确认应用容器处于等待状态 |
| 3 | K8s State | kubernetes (fact-61b3821e08ab, fact-a424d6f65a19) | pod.status: Pending; pod.phase: Pending | 确认整个 Pod 生命周期被阻塞在调度完成后的阶段 |
| 4 | K8s Config | kubernetes (fact-12401c0ffbc5, fact-59438cd2b69f) | container.resource_request.memory: 8Mi; container.resource_limit.memory: 32Mi | 排除内存不足导致的调度或启动失败，提供上下文 |
| 5 | Metric | prometheus (fact-90b77a36b4d5) | kube_pod_container_status_waiting_reason: 1 (reason: ContainerCreating) | 在监控层印证了 Pod 等待状态的客观存在 |
| 6 | Metric | prometheus (fact-a69b5384ad65) | kube_pod_container_status_restarts_total: 0 | 确认 Pod 在故障期间未发生任何重启，处于初始阻塞点 |

Kubernetes 事件与状态事实 (1, 2, 3) 形成了完整闭环：事件日志明确指出是 ConfigMap 缺失导致 `input` 卷挂载超时，这直接解释了为什么 Pod 停留在 `Pending` 状态且容器一直未被启动。监控数据 (5, 6) 在系统层面印证了这一静态阻塞现象，排除了容器频繁重启或状态跳变的可能性。资源上下文 (4) 证实了该 Pod 的资源请求极其保守，排除了资源不足导致的次生故障。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 在 aiops-case-03 命名空间中缺失 → Kubelet 挂载 'input' 卷失败 → Volume Mount 持续报错阻断容器创建 → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论
已确认根因为 Pod 定义中引用的 ConfigMap `unavailable-config` 在当前命名空间中不存在。

**证据支撑**：
1. **直接证据**：Kubernetes Event 日志 (fact-d556c14e8f2e) 明确报错 `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found`。
2. **状态印证**：Pod 长时间处于 `ContainerCreating` 等待状态 (fact-65594218e962)，且没有重启记录 (fact-a69b5384ad65, restart_count: 0)，符合启动前依赖项（ConfigMap）缺失导致的静态阻塞特征。
3. **排除干扰**：系统资源请求极低 (fact-12401c0ffbc5, memory: 8Mi)，且监控未见相关 OOM 或调度失败指标，排除了资源竞争因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.1s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 39.5s (Evidence 30.9s, RCA 8.5s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
