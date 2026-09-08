## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w in namespace aiops-case-03 stuck in status ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (多次出现) | 定位核心故障：指定的 ConfigMap 不存在，直接导致卷挂载失败 |
| 2 | K8s State | kubernetes | Pod 状态 `Pending`，容器状态 `ContainerCreating`，重启次数 `0` | 确认容器未启动，挂载阻塞是造成停滞的直接表现 |
| 3 | K8s Config | kubernetes | Pod spec 中定义卷 `input`，请求 CPU `5m`/内存 `8Mi`，限制 CPU `50m`/内存 `32Mi` | 排除资源不足因素，确认为配置依赖缺失引发的阻塞 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 `1` | 从监控侧印证 Pod 长期处于等待状态 |

当前证据显示，Kubelet 因挂载卷 `input` 失败而反复阻塞容器启动。K8s 事件明确指出失败原因是 ConfigMap `unavailable-config` 不存在。Metrics 和 K8s 状态均确认 Pod 处于 Pending 状态且未进行任何重启尝试，排除了启动后崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → 卷挂载失败 → 容器无法启动 → Pod 保持 Pending/ContainerCreating 状态
```

### 根因结论

已确认的根因是：Pod 的卷配置引用了不存在的 ConfigMap `unavailable-config`。

证据链闭环如下：
1. **K8s Event**（证据 #1）明确记录了 `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found`，这是挂载失败的直接原因。
2. **K8s State**（证据 #2）显示容器处于 `ContainerCreating` 状态且重启次数为 `0`，符合挂载配置缺失导致的启动前阻塞特征。
3. **Metric**（证据 #4）与日志事件相互印证，证实该状态在观测期内持续存在。

因此，集群中 Pod 的挂载失败完全由缺失的 ConfigMap 配置引起。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 65.6s
├─ 并发证据采集: 55.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 55.4s (Evidence 47.8s, RCA 7.5s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
