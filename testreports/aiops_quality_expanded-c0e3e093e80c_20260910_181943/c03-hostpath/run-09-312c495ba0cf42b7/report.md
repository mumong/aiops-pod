## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 定义中挂载的 hostPath 卷 'input' 所指向的目标路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 在调度节点 node2 上不是目录（类型检查失败），导致 kubelet 无法完成卷挂载准备（Setup），容器因卷依赖阻塞而处于 ContainerCreating 等待状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接证据：kubelet 报告目标路径非目录，卷挂载（Setup）失败 |
| 2 | K8s State | kubernetes | `pod.phase: Pending`, `containers_waiting_reason: ContainerCreating`, `restart_count: 0` | 状态事实：Pod 处于挂载阻塞等待期，容器尚未拉起，无重启记录 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu: 5m, memory: 8Mi`, `container.resource_limit.cpu: 50m, memory: 32Mi` | 上下文事实：排除资源不足（OOM/压力）导致 Pod 启动失败的可能性 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason: ContainerCreating) = 1 | 独立观测：确认 Pod 长期处于挂载阻塞状态，无业务流量发生 |

**证据说明：**
- 证据 1 (Event) 指出了容器阻塞的直接物理原因（hostPath 类型检查失败），解释了证据 2 中 Pod 状态停留在 `Pending` / `ContainerCreating` 的机制。
- 证据 3 (Config) 提供的极低资源请求量与证据 1 的存储错误形成对照，排除了资源竞争导致挂载失败的假设。
- 证据 4 (Metric) 在系统层面复现了容器未就绪且处于等待期的事实，与 K8s 事件和状态相互印证，确认该故障为持续性阻塞而非瞬时异常。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义的 hostPath 卷配置指向 node2 上的文件(非目录) → kubelet 卷挂载前置类型检查失败(Setup阻塞) → 容器无法完成挂载准备 → Pod 处于 ContainerCreating 等待状态
```

### 根因结论

已确认根因为：**Pod `aiops-case-v06/workload` 挂载的 hostPath 卷 'input' 所指向的目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度节点 `node2` 上不是一个目录。**

证据编号 1 显示 `hostPath type check failed`，表明调度节点上的该路径存在但与 Pod 定义的目录类型不符（通常为已存在的普通文件或符号链接）。这导致 `kubelet` 在卷挂载阶段（Setup）阻断并持续重试，引发证据 2、4 中观测到的容器长期处于 `ContainerCreating` 且无重启的现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.6s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-v06/workload: 45.5s (Evidence 38.5s, RCA 7.0s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
