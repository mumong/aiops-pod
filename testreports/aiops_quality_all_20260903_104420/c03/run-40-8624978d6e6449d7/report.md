## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 ContainerCreating 状态且无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-11a3ff5fe414) | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (x45) | 直接指明 Pod 定义的 Volume 绑定的 ConfigMap 在集群中不存在 |
| 2 | K8s Event | kubernetes (fact-226afb198f33) | `timed out waiting for the condition` (unmounted volumes=[input]) | 确认 Kubelet 因上述挂载失败陷入持续重试和超时状态 |
| 3 | K8s State | kubernetes (fact-41dae2af03ac) | container `app` waiting_reason: `ContainerCreating` | 描述容器的当前阻塞状态 |
| 4 | Metric | prometheus (fact-6db5ae00e727) | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` | 观测数据印证容器处于等待状态 |
| 5 | Metric | prometheus (fact-d97aeae722f5) | `kube_pod_container_status_restarts_total{container="app"} = 0` | 排除因 CrashLoopBackOff 或重启导致的启动失败，佐证是挂载阻塞 |

**证据说明**：
事件日志 (fact-11a3ff5fe414, fact-226afb198f33) 提供了直接的失败原因（ConfigMap 缺失导致挂载超时），而 Kubernetes 状态 (fact-41dae2af03ac) 与 Prometheus 指标 (fact-6db5ae00e727, fact-d97aeae722f5) 提供了对 `ContainerCreating` 状态的横向验证。三者结合，锁定了导致 Pod 无法进入 Running 状态的唯一障碍。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Kubelet 挂载 Volume 'input' 失败 → 容器 'app' 卡在 ContainerCreating 状态 → Pod 状态为 Pending / ContainersNotReady
```

### 根因结论

**已确认的根因**：Pod `workload-5b5fc86c8c-zz82w` 的 YAML 定义中挂载了名为 `input` 的 Volume，该 Volume 依赖名为 `unavailable-config` 的 ConfigMap。由于该 ConfigMap 在 `aiops-case-03` 命名空间中不存在（证据编号 #1），Kubelet 无法完成挂载并陷入持续超时（证据编号 #2），导致容器 `app` 永远停留在 `ContainerCreating` 状态（证据编号 #3, #4）。

日志和 Tracing 未提供额外信息是因为容器物理上未能启动，但这并不影响上述结论的成立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.1s
├─ 并发证据采集: 48.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 48.2s (Evidence 40.9s, RCA 7.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed
