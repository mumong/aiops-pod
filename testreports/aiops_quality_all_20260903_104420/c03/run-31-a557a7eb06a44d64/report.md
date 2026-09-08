## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w stuck in ContainerCreating state (Pending phase). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` (x35 over 56m) | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接定位挂载失败的根因：ConfigMap 缺失 |
| 2 | K8s State | `kubelet` (Pod Condition) | `ContainersNotReady: "containers with unready status: [app]"` | 确认容器长时间处于非就绪状态 |
| 3 | K8s State | `container.waiting_reason` | `reason: "ContainerCreating"` | 明确当前的阻塞阶段，非 CrashLoopBackOff |
| 4 | K8s Event | `kubelet` (x20 over 54m) | `Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 证实挂载操作在较长时间内持续超时 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = `1` (reason=`ContainerCreating`) | 从监控维度独立印证 Pod 持续等待中 |
| 6 | K8s Config | `container.resource_request` | `memory: 8Mi`, `cpu: 5m` | 提供资源请求量作为排错背景 |

**证据分析：**
Kubernetes 维度事实（编号 1、2、3）与 Prometheus 监控数据（编号 5）高度一致，均指向同一异常状态（`ContainerCreating` 且 `ContainersNotReady`）。事件记录（编号 1 和 4）明确指出了具体失败原因（`configmap "unavailable-config" not found`），直接排除了资源不足或节点亲和性等常见调度问题。缺失的 Logging/Tracing 工具调用（因 Pod 未启动）不影响上述状态的判定。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-03' 中 ConfigMap 'unavailable-config' 不存在 → Kubelet 尝试挂载引用该 ConfigMap 的 Volume 'input' 失败 → 挂载超时且配置未就绪 → Pod 持续停留在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` 处于 `ContainerCreating` 状态无法启动。
- **原因**：Pod 的 Volume `input` 配置引用了一个不存在的 ConfigMap（`unavailable-config`）。
- **事实支撑**：
  - Kubelet 事件记录明确指出 `MountVolume.SetUp failed ... configmap "unavailable-config" not found`（证据 #1、#4）。
  - Pod 状态及监控数据确认了容器持续处于 `ContainerCreating` 等待阶段（证据 #2、#3、#5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 17.8s
├─ 并发证据采集: 68.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 68.5s (Evidence 60.7s, RCA 7.7s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
