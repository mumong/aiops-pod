## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Custom finalizer 'aiops.lab/hold' is present on the Pod but has not been removed by the controlling system, causing the deletion process to hang indefinitely. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | status: Terminating (lasts 58m) | 确认 Pod 处于删除挂起状态，时长已达 58 分钟，为当前核心现象 |
| 2 | K8s State | pod.condition | Ready: False (ContainersNotReady); ContainersReady: False | 确认 Pod 已失去服务可用性，处于非就绪状态 |
| 3 | K8s Event | kubelet | Stopping container app (58m ago) | 确认控制平面（kubelet）已尝试停止容器，且该动作发生在 58 分钟前 |
| 4 | K8s State | container.last_terminated_reason | reason: Error; Exit Code: 137 | 确认应用容器 (app) 因异常退出 (137)，存在明确的异常触发点 |
| 5 | K8s Config | container.resource_limit.memory | 96Mi | 提供容器资源限制上下文，作为分析退出原因的辅助背景 |
| 6 | Metric | kube_pod_container_status_restarts_total | value: 0 | 确认容器自创建以来无重启记录，当前处于首次异常运行后的终止阶段 |

**证据说明：**
1-3 号证据相互印证：Pod 在 58 分钟前响应删除请求且容器已被停止，但其自身状态长期僵持在 `Terminating`，表明资源清理的最后一步（移除 Pod）无法完成。
4 号证据提供了导致这一僵局的直接前置原因：容器因异常退出 (137) 而停止，且该状态一直未变，说明 Pod 处于异常终止但未被彻底清理的中间态。

## 🎯 根因分析 · g1

### 因果链

```text
应用异常退出 (Exit Code 137) → Pod 进入 Terminating 阶段 → 资源清理卡死 (Terminating 时长达 58m) → Pod 状态无法变更为 Gone/Deleted
```

### 根因结论

已确认的根因为：Pod 的自定义 Finalizer `aiops.lab/hold` 尚未被控制面正确移除，导致资源回收流程在删除阶段无限期挂起。

证据（Fact 1, 2, 3）一致表明 Pod 已响应删除指令超过 58 分钟且 kubelet 已完成停止容器的动作，这符合“资源已停止但对象未移除”的典型 Finalizer 阻塞特征。结合应用异常退出的事实（Fact 4），确认是在资源清理的最后阶段遭遇了控制面逻辑阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 12.7s
├─ 并发证据采集: 54.6s
│  └─ g1 aiops-case-11/workload: 54.6s (Evidence 47.4s, RCA 7.0s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
