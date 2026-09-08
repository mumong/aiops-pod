## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 ContainerCreating/Pending 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (如 fact-573c90063526) | 明确显示 kubelet 因找不到 ConfigMap 导致挂载失败，直接定位根因 |
| 2 | K8s State | `kubelet` | `Waiting Reason: ContainerCreating` (fact-f83371273998) | 确认 Pod 卡在容器启动阶段，未进入运行态 |
| 3 | K8s State | `kubelet` | `Pod Status: Pending` (fact-1f07ef55a27e) | 验证 Pod 处于待调度后的挂起状态，未就绪 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1, labels: `reason="ContainerCreating"` (fact-a75b54f87b23) | 独立验证容器处于 Waiting 状态且原因为 ContainerCreating |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 0 (fact-1edcd689fc98) | 排除因 OOM 等导致的反复重启现象 |

证据 1 中的失败事件是决定性证据，直接指出 Volume 'input' 挂载失败；证据 2 和 4 在状态层面与事件原因相互印证，证实容器卡在创建期；证据 5 确认了这是一个首次发生的静态配置错误，而非运行时资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
Volume 'input' 引用不存在的 ConfigMap 'unavailable-config' → kubelet MountVolume.SetUp 失败 → 容器无法挂载存储，无法启动 → Pod 保持 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因是 Pod spec 中 Volume 'input' 引用了 namespace `aiops-case-03` 中不存在的 ConfigMap `unavailable-config` [证据 1]。该缺失导致 kubelet 的挂载前置检查失败，容器启动逻辑被阻断，表现为 Pod 卡在 `ContainerCreating` 状态且无重启行为 [证据 2、4、5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.9s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.4s (Evidence 38.5s, RCA 8.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
