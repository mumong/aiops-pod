## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 处于 Pending/ContainerCreating 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount` (x23 over 40m): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指出挂载失败的物理原因是 ConfigMap 缺失 |
| 2 | K8s State | kubelet | `ContainerCreating`: `containers with unready status: [app]` | 确认容器创建阶段因前置依赖阻塞而停滞 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1`: `reason=ContainerCreating` (timestamp: 2026-09-10T13:37:02.721000Z) | 监控确认 Pod 处于等待状态，且原因为挂载阶段而非 OOM 或 CrashLoop |
| 4 | K8s Config | kubelet | `container.resource_request.memory=8Mi`, `container.resource_limit.memory=32Mi` | 资源请求极低，可排除因资源不足导致的资源抢占或调度失败 |

- **印证关系**：Kubernetes 事件（#1）明确提供了失败原因（ConfigMap 缺失），Metric（#3）的等待原因与 K8s 事件中的状态完全一致。容器未启动（#2）与无应用日志/Trace 的采集结果（`not_applicable`）在逻辑上相互印证，排除了应用层运行期故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 声明 non-optional volume 挂载 ConfigMap 'unavailable-config' → ConfigMap 'unavailable-config' 在 namespace 中缺失 → kubelet 执行 MountVolume.SetUp 失败并超时 → 容器 runtime 无法启动，Pod 停留在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：Pod 定义的 Volume `input` 引用了 ConfigMap `unavailable-config`，该 ConfigMap 在当前 namespace 中不存在且未标记为 `optional`。这导致 kubelet 在启动容器前无法完成挂载准备，持续触发 `FailedMount` 错误，从而阻塞了容器创建，表现为 Pod 一直处于 `ContainerCreating` 状态。

**证据支撑**：
- 依据事实 `fact-ae55f38e2ed7`，Kubelet 日志明确记录因 ConfigMap 缺失导致挂载失败，并重复出现了 23 次。
- 依据事实 `fact-566bb79f984e`，Metric 数据确认了 Pod 的等待原因与 Kubernetes 内部状态一致，且重启次数为 0，排除了其他应用运行期故障。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 17.5s
├─ 并发证据采集: 546.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 546.8s (Evidence 538.7s, RCA 7.9s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-sandbox-create-failed, pod-imagepull-failed
