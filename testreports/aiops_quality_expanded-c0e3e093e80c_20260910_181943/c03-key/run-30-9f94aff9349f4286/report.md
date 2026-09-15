## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating/Pending 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-2de1486f7742` | `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 直接确认导致 Pod 停滞的具体挂载失败原因 |
| 2 | K8s State | `fact-baea5ea44836` | `container.waiting_reason: ContainerCreating` (容器: `app`) | 证实 Pod 处于初始挂载阶段，未能进入运行态 |
| 3 | K8s State | `fact-66366f3824c4` | `container.status.ready: False` (`ContainersNotReady`) | 佐证容器未能完成初始化并启动就绪检查 |
| 4 | Metric | `fact-495b5c27b0fd` | `kube_pod_container_status_waiting_reason=1` (reason: `ContainerCreating`, 样本: 1) | 从监控维度再次验证容器卡在等待挂载的状态 |

证据链相互印证：Kubernetes 事件 (证据 1) 提供了确凿的技术细节，解释了指向不存在的 ConfigMap key (`unavailable-key`) 导致挂载失败；Kubernetes 状态 (证据 2, 3) 与 Prometheus 指标 (证据 4) 一致显示容器卡在 `ContainerCreating/ContainerCreating` 阶段。由于日志和 Tracing 未开启（容器未启动），核心判断基于基础设施层的挂载事件与状态。

## 🎯 根因分析 · g1

### 因果链

```text
Volume 'input' 引用不存在的 key 'unavailable-key' → MountVolume.SetUp 失败 → Pod 无法挂载卷，持续处于 ContainerCreating 状态 → 容器无法启动
```

### 根因结论

已确认的根因为：Pod 规范中 Volume `input` 配置引用了 ConfigMap 中不存在的 Key `unavailable-key`，导致 kubelet 挂载卷失败。
- 证据 1 (K8s Event) 明确指出 `configmap references non-existent config key: unavailable-key`。
- 证据 2, 3, 4 证实了该失败导致的持续现象（状态为 `ContainerCreating` / `ContainersNotReady`）。
- 资源限制 (Memory/CPU) 与重启次数 (证据 4) 均为正常状态或无关因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 42.6s
├─ 并发证据采集: 32.5s
│  └─ g1 aiops-case-v05/workload: 32.5s (Evidence 25.0s, RCA 7.4s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
