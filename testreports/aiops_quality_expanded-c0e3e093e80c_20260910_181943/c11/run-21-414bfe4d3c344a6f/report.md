## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 因 metadata.finalizers 中存在 'aiops.lab/hold' 自定义 finalizer 而处于 Terminating 状态。虽然容器已在 41 分钟前因 SIGKILL (exitCode 137) 终止且节点 Ready，但 API Server 必须等待该 finalizer 的持有者释放资源后才会执行对象删除操作。该 finalizer 持有者（推测为自定义控制器）未能完成清理或响应删除请求，导致 Pod 卡死。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | Terminating (lasts 41m) | 确认当前 Pod 处于卡死状态，且持续时间较长 |
| 2 | K8s Event | event.message | Stopping container app (41m ago), Exit Code: 137 | 表明容器早在 41 分钟前已因 SIGKILL 终止，但状态未清除 |
| 3 | K8s State | pod.condition | Ready=False, ContainersReady=False, reason="ContainersNotReady" (16m ago) | 证明容器已停止运行，节点状态与 Pod 元数据状态存在冲突 |
| 4 | K8s State | pod.phase | Running | 反映 API Server 的 etcd 中仍将该 Pod 对象维持在工作负载中 |
| 5 | K8s Event | event.message | Killing | 确认 kubelet 已经执行了删除容器的动作 |
| 6 | K8s Config | container.resource_limit.memory | 96Mi (limit), 24Mi (request) | 排除明显内存超限的常规 OOMKilled 场景，提示 Exit 137 可能由外部信号触发 |
| 7 | Metric | kube_pod_status_phase | Running=1 (at 04:28:48) | 侧面印证 API Server 视角的对象状态未被更新或清理 |
| 8 | Metric | kube_pod_container_status_restarts_total | 0 (at 04:28:48) | 证明该 Pod 启动后没有发生过自动重启，符合 Terminating 阶段特征 |

上述证据表明，虽然底层容器（由 kubelet 管理）已因异常被清理（Exit 137），但控制平面的 Pod 对象并未完成删除流程。`phase: Running` 与 `exit_code: 137` 的同时存在，以及长达 41 分钟的 `Terminating` 滞留，是典型的资源未正确释放导致的死锁现象。

## 🎯 根因分析 · g1

### 因果链

```text
metadata.finalizers 存在自定义 finalizer 'aiops.lab/hold' → Kubernetes API Server 阻止 Pod 对象从 etcd 物理删除 → Pod 对象卡在 Terminating 状态且 phase 显示 Running → 用户可见 Pod 无法删除且状态异常
```

### 根因结论

已确认的根因为自定义 Finalizer `'aiops.lab/hold'` 的持有者（通常为特定的 Operator 或 Controller）未能响应或完成删除清理逻辑。

1. **直接机制**：Kubernetes 在删除 Pod 时，如果发现 `metadata.finalizers` 中包含未被移除的条目，API Server 会阻止该对象从 etcd 中删除。
2. **现象印证**：
    - 容器早在 41 分钟前已被 kubelet 杀掉（`Exit Code: 137`）[证据 #2, #5]。
    - 但 Pod 元数据状态仍显示为 `Terminating` 且 `phase: Running` [证据 #1, #4]。
    - 资源已释放但对象未移除，符合 Finalizer 未清理导致的典型特征。

目前证据不足以确认 `'aiops.lab/hold'` 的具体持有组件状态（Logging/Tracing 缺失），但基于 K8s 状态事实，最终根因指向该自定义 Finalizer 持有者未能完成清理。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.9s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-11/workload: 36.1s (Evidence 27.4s, RCA 8.6s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
