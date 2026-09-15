## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 定义中 Volume 'input' 引用了不存在的 ConfigMap 'unavailable-config' 且设置为 Required (Optional: false)，导致 kubelet 持续挂载失败，容器无法创建。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-5ec5a3e1e2cb) | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 致命证据：指出挂载失败直接源于缺失 ConfigMap |
| 2 | K8s Event | kubernetes (fact-599ff0552e82) | `Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 辅助证据：说明 kubelet 因超时持续重试挂载失败 |
| 3 | K8s State | kubernetes (fact-39cb0919c182) | `Pod Status: Pending` | 现象确认：Pod 处于等待状态，未进入容器运行阶段 |
| 4 | Metric | prometheus (fact-566efa5498ae) | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` | 状态印证：确认应用容器处于创建前的等待阶段 |

**证据关联分析：**
Kubernetes 事件 `fact-5ec5a3e1e2cb` 与 `fact-599ff0552e82` 互为表里，明确了 Pod 停滞在 `Pending` 状态的具体阻塞点在于 `input` 卷挂载。指标数据 `fact-566efa5498ae` 中的 `ContainerCreating` 等待原因进一步佐证了 Pod 未因资源限制（如 CPU/Memory）调度失败，而是因为基础设施依赖缺失导致无法完成启动前置步骤。

## 🎯 根因分析 · g1

```text
应用 Pod 定义中将 Volume 'input' 绑定至不存在的 ConfigMap 'unavailable-config' 且未设置 Optional: true → kubelet 尝试挂载该 ConfigMap 失败并持续超时重试 → Pod 阻塞在 volume 挂载阶段，容器无法创建 (ContainerCreating) → 应用无日志输出且无重启行为
```

**根因结论：**
已确认根因为 **配置缺失导致的挂载阻塞**。
集群中不存在名为 `unavailable-config` 的 ConfigMap，而 Pod `workload-5b5fc86c8c-xn974` 的 `input` 卷强制依赖该 ConfigMap（证据编号 1、2）。这一配置错误导致 kubelet 挂载卷操作超时失败（证据编号 2），致使 Pod 停留在 `Pending` 状态（证据编号 3）且容器处于 `ContainerCreating` 等待中（证据编号 4），未能进入应用运行生命周期。

---

## 📊 性能统计

```text
├─ 总耗时: 10.1m
├─ 问题定位: 40.1s
├─ 并发证据采集: 557.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 557.2s (Evidence 552.5s, RCA 4.6s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- 未调用 Runbook
