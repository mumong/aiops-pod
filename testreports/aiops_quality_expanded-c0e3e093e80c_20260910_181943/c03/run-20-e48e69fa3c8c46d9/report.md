## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 长期处于 ContainerCreating 状态，未启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | phase: `Pending`; status: `Pending`; condition: `Ready=False (ContainersNotReady)` | 确认 Pod 未进入运行态 |
| 2 | K8s Event | kubelet | `FailedMount`: "configmap \"unavailable-config\" not found" (x35 over 59m) | 直接定位挂载失败的具体对象 |
| 3 | K8s Event | kubelet | `FailedMount`: "Unable to attach or mount volumes: unmounted volumes=[input]..." (x20 over 56m) | 证实 Volume `input` 持续挂载失败 |
| 4 | K8s State | Kubernetes | container `app` waiting reason: `ContainerCreating` | 容器等待启动，与 Phase 异常一致 |
| 5 | K8s State | Kubernetes | restart_count: `0` | 容器从未启动过，排除启动后崩溃 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = `1` | 从监控侧验证容器长期处于等待状态 |

**证据关联说明：**
Kubernetes Event 直接揭示了 `configmap "unavailable-config"` 缺失导致 Volume `input` 挂载失败（证据 2-3）。该失败导致 Pod 阶段保持在 `Pending`（证据 1），进而引发容器 `app` 无限期处于 `ContainerCreating` 的 Waiting 状态且未发生过重启（证据 4-5）。Metric 数据（证据 6）与 K8s 状态相互印证了该持续现象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用不存在的 ConfigMap 'unavailable-config' → kubelet 挂载 Volume 'input' 时查找失败 → MountVolume.SetUp 报错 → 容器 'app' 持续处于 ContainerCreating 状态，Pod 卡在 Pending
```

### 根因结论

已确认根因为 **Pod 配置中引用的 ConfigMap 'unavailable-config' 不存在**。

依据：
- K8s Event 明确指出挂载 Volume "input" 时因缺少 ConfigMap "unavailable-config" 而失败（证据 2）。
- Volume `input` 挂载失败导致容器 `app` 无法正常创建，处于等待状态且未重启（证据 4-5）。
- 监控数据证实了该状态的持续性（证据 6）。

当前证据链完整，可排除资源限制或网络问题，根因直接指向配置缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 20.5s
├─ 并发证据采集: 121.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 121.4s (Evidence 113.9s, RCA 7.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed, pod-config-error, pod-volume-mount-failed, pod-sandbox-create-failed
