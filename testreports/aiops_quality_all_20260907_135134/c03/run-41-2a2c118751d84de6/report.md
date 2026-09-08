## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 Pending/ContainerCreating 状态，无法进入 Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-61120ad2ab8e) | 直接指出挂载卷失败的具体原因：ConfigMap 缺失 |
| 2 | K8s State | `kubernetes` | Pod status: `Pending` (fact-1831c0f1efe7) | 描述 Pod 当前停滞的宏观状态 |
| 3 | K8s State | `kubernetes` | Container `app` waiting reason: `ContainerCreating` (fact-a060245071a5) | 细化容器停滞的阶段，表明卡在资源准备期 |
| 4 | K8s Config | `kubernetes` | Volume `input` 配置引用 `configmap "unavailable-config"` (fact-61120ad2ab8e) | 暴露故障源头：配置中引用的资源不存在 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` for `ContainerCreating` (fact-0b56bd59b130) | 独立确认容器处于创建等待状态，支持事件结论 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total=0` (fact-fde796d28017) | 确认应用尚未启动，排除了运行后重启的可能性 |

证据表明：Kubernetes 事件与监控指标高度一致。Event 记录了具体的挂载失败原因（ConfigMap 不存在），Metric 确认了容器一直处于 `ContainerCreating` 且重启次数为 0 的状态。Pod 状态处于 `Pending`，说明容器尚未进入 Running 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Kubelet 执行 MountVolume.SetUp 找不到对象 → Volume 'input' 挂载失败 → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的 `Volume 'input'` 定义中引用了 ConfigMap `unavailable-config`，但该 ConfigMap 在 `aiops-case-03` 命名空间中不存在。

该配置错误导致 Kubelet 在启动容器前无法完成挂载操作，引发 `FailedMount` 错误。由于挂载是启动前置条件，Pod 因此停滞在 `Pending` 状态，容器处于 `ContainerCreating` 阶段。证据编号 1、2、3、4、5 均相互印证了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 36.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 36.4s (Evidence 28.3s, RCA 8.0s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-sandbox-create-failed
