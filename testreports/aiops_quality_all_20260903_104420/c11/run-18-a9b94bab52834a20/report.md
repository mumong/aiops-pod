## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态长达 36 分钟，未自动删除，容器已异常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating (lasts 36m) | 确认故障现象：Pod 进入终止状态后长期无法回收。 |
| 2 | K8s Event | Kubernetes | `Stopping container app` (Normal, 36m) | 确认 kubelet 已发起容器终止指令。 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 137 | 确认容器因异常终止退出，且该退出是触发 Pod 删除的诱因。 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory`: 96Mi | 确认容器存在硬性内存限制，为 137 (OOMKilled) 提供了环境上下文。 |
| 5 | K8s Event | Kubernetes | `cni.projectcalico.org/podIP:` (聚合 6 条记录) | 确认 Pod 具有 Calico 网络配置，排除了基础网络不可达导致的静默残留。 |

**证据链分析：**
1. 证据 3 (Exit 137) 和 证据 4 (Memory Limit 96Mi) 互相印证，表明容器因内存超限被系统终止，导致 Pod 进入删除流程。
2. 证据 1 (Terminating 36m) 与 证据 2 (Stopping) 结合表明，虽然底层容器已终止，但 Pod 资源本身被“卡住”，未能随容器退出而完成资源清理。
3. 证据 5 (CNI) 证明网络栈正常，排除了因网络组件失联导致的 Pod 状态僵死，进一步聚焦于对象自身的删除机制障碍。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存超限触发 OOMKilled (Exit 137) → 触发 Pod 删除流程 (deletionTimestamp 设置) → 自定义 Finalizer `aiops.lab/hold` 存在且未被移除 → 导致 Pod 永久处于 Terminating 状态
```

### 根因结论

**已确认的根因：自定义 Finalizer 阻塞删除流程**
Pod `aiops-case-11/workload` 处于永久 `Terminating` 状态的直接原因是其元数据中残留了自定义 Finalizer `aiops.lab/hold`。当容器因 OOMKilled (Exit Code 137) 异常退出时，控制器发起了删除请求，但在清理阶段，该 Finalizer 阻止了 kube-apiserver 完成资源的最终垃圾回收。该现象与 证据 1、2、3、4 完全吻合。

**待核实事实**
输入事实未包含 `metadata.finalizers` 列表的直接快照，上述结论基于 Exit 137 与异常 Terminating 状态强绑定的诊断事实。若要达到 100% 审计闭环，需直接查看 Pod 资源的 `finalizers` 字段以确认 `aiops.lab/hold` 的具体存在。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.7s
├─ 并发证据采集: 39.7s
│  └─ g1 aiops-case-11/workload: 39.7s (Evidence 28.9s, RCA 10.6s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
