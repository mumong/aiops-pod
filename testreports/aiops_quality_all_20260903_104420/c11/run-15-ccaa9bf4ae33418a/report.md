## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态已超过 32 分钟，容器已退出，但 Pod 未被删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet event | 32m Killing app (Stop container) | 指示容器被系统强制终止，触发 Pod 生命周期进入终止流程 |
| 2 | K8s State | pod.state | app exit_code 137 | 证实容器进程因被接收 SIGKILL 信号而异常退出 |
| 3 | K8s State | pod.condition | Ready=False, ContainersNotReady: [app] | 确认容器不处于就绪状态，Pod 无法继续提供服务 |
| 4 | K8s State | pod.status | phase=Running, status=Terminating (32m) | 核心异常事实：Pod 对象停留在终止阶段超过 30 分钟，无法完全移除 |
| 5 | K8s State | pod.config | resource_request: 20m/24Mi, resource_limit: 200m/96Mi | 资源申请较小，非资源耗尽导致异常 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total=0 (app) | 确认该容器未发生重启（restart_count=0），进程退出后未被重启策略再次拉起 |

证据 4 与证据 1、2 形成矛盾：Kubernetes API Server 收到了终止信号并停止了容器，但 Pod 对象状态停滞在 `Terminating`。由于证据 6 确认没有重启发生，Pod 必须被完全清理才能进入 `Failed` 或 `Succeeded` 状态，停滞表明存在阻止 API Server 删除 Pod 对象资源的机制。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 删除请求触发 finalizer 'aiops.lab/hold' → kubelet 强制终止容器(app exit 137) → finalizer 控制器未及时移除 'aiops.lab/hold' → API Server 阻塞删除 Pod 资源 → Pod 对象卡在 Terminating (32m+)
```

### 根因结论

**根因确认**：Pod `aiops-case-11/workload` 卡在 `Terminating` 状态是由于定义了自定义 Finalizer `'aiops.lab/hold'`，且对应的控制器（或 Operator）在容器 `app` 退出后未能及时执行清理逻辑来移除该 Finalizer，导致 Kubernetes API Server 无法完成对象的生命周期删除。

- **支撑事实**：K8s 机制规定只有当 Pod 的 `spec.finalizers` 列表为空时，API Server 才会真正删除对象；Pod 状态停滞且无重启（`fact-2a451b4b34a7`）证实了生命周期被外部机制锁定。
- **证据不足项**：缺失最终控制器或 Operator 在处理该 Finalizer 时的具体日志和报错信息，因此无法进一步断定是控制器代码缺陷、网络通信问题还是其他配置错误导致了清理逻辑的失效。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 19.3s
├─ 并发证据采集: 549.8s
│  └─ g1 aiops-case-11/workload: 549.8s (Evidence 538.4s, RCA 11.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
