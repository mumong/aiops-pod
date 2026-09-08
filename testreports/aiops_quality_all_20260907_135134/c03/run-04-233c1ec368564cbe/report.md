## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 Pending 状态，容器处于 ContainerCreating 状态且未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-dcc87730c4f9) | 提供启动阻塞的直接报错原因 |
| 2 | K8s State | kubernetes | 容器 `app` 处于等待状态，原因 `ContainerCreating` (fact-0a9b6637cdd9) | 对应启动阶段的停滞现象 |
| 3 | K8s State | kubernetes | Pod 总状态为 `Pending`，条件 `ContainersReady` 为 `False` (fact-4697bca7fce2, fact-62945ab81eb6) | 确认 Pod 尚未进入运行期 |
| 4 | K8s Config | kubernetes | 容器 `app` 请求资源：CPU 5m, 内存 8Mi；限制：CPU 50m, 内存 32Mi (fact-04173a67b1cc, fact-49e36b2da564 等) | 排除资源超卖导致的调度失败 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 为 1，标签 `reason=ContainerCreating` (fact-b19bf29072cb) | 独立监控数据印证 K8s 状态 |

证据表明 Pod 未处于资源竞争导致的调度等待，而是卡在挂载卷阶段。Metric 等待原因与 K8s Event 报错完全一致，排除应用日志与 Trace（因容器未启动）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 ConfigMap 'unavailable-config' → kubelet MountVolume.SetUp 失败 → 容器保持 ContainerCreating 状态，Pod 保持 Pending → 业务不可用
```

### 根因结论

已确认的根因为 Pod Spec 中定义的 Volume 引用了不存在的 ConfigMap `unavailable-config`。

这一缺失导致 kubelet 在执行挂载操作时因找不到配置项而失败，直接阻断了容器的启动流程。该结论由 K8s Event 记录的报错信息以及容器始终处于 `ContainerCreating` 状态的事实（证据 #1, #2, #5）相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 38.4s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 39.6s (Evidence 30.5s, RCA 9.0s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
