## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload 处于 ContainerCreating 状态，挂载 HostPath 卷失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 揭示挂载失败的直接原因：目标路径缺失或类型不符 |
| 2 | K8s Event | Kubernetes | `timed out waiting for the condition` (unmounted volumes=[input]) | 证明挂载卷因上述原因导致 Pod 无法继续调度进入运行状态 |
| 3 | K8s State | Kubernetes | Pod 状态 `Pending`，容器 `app` 等待原因 `ContainerCreating` | 确认异常处于挂载卷处理阶段，容器未启动 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 指标层面验证了容器处于因资源/环境未就绪而挂起的状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 排除因应用崩溃导致的重启，故障发生在启动前置阶段 |

**证据关联说明：**
Kubernetes 事件（#1, #2）明确指出了挂载卷失败的根本原因是宿主机路径校验不通过；K8s 状态（#3）证实了该失败导致 Pod 停滞在 Pending 阶段。Metric 数据（#4, #5）从独立维度佐证了这一现象：等待原因指标为 ContainerCreating，且重启计数为 0，排除了其他类型的运行期异常。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机 node2 路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在非目录对象 → Kubelet 执行 hostPath 卷挂载前 type check 失败 → Pod 卷挂载阶段报错并超时 → Pod 卡在 Pending 状态，应用服务不可用
```

### 根因结论

已确认的根因为 Pod 定义中 `HostPath` 卷指向的宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度目标节点（node2）上不存在或不是有效的目录，导致 Kubelet 在挂载卷的 `type check` 阶段直接失败（证据 #1, #2）。此失败阻断了容器的初始化流程，表现为 Pod 处于 `Pending` 且容器状态为 `ContainerCreating`（证据 #3, #4）。

关于该路径缺失的具体运维背景（如是否被误删、路径配置错误等）当前无直接证据支持，标记为未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.7s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-v06/workload: 40.3s (Evidence 31.8s, RCA 8.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-sandbox-create-failed
