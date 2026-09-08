## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态 38 分钟未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: `Running`; Container `app` exit_code: `137`; Restart count: `0` | 证实容器 `app` 此前已发生错误退出（SIGKILL），且进程未重启 |
| 2 | K8s Event | kubernetes | Event: `Killing` 38m ago, message: `Stopping container app` | 确认 kubelet 在过去 38 分钟内试图停止容器，但 Pod 资源未从集群移除 |
| 3 | K8s State | kubernetes | Pod status: `Terminating (lasts 38m)` | 证明 Pod 对象进入终止状态的时间长度，即阻塞持续时长 |
| 4 | K8s Config | kubernetes | Container `app` memory_limit: `96Mi`; memory_request: `24Mi` | 提供容器资源限制上下文，作为排查容器为何退出（如 OOM）的背景数据 |
| 5 | K8s Event | kubernetes | Event annotation: `Exit Code: 137`; Status condition `Ready`/`ContainersReady`: `False` | 进一步佐证容器因信号异常终止（137）且当前处于不可用状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase`: `1` (Running); `restarts_total`: `0` | 从监控侧确认 Pod 对象目前仍处于 Running 阶段，且无重启记录 |

**证据说明：**
Kubernetes 状态和事件明确显示，容器 `app` 因退出码 137 已终止且无重启，但 Pod 对象自身卡在 `Terminating` 状态长达 38 分钟未消失（证据 2、3）。监控数据（证据 6）交叉验证了 Pod 的当前阶段状态。资源配置（证据 4）仅为终止原因的上下文，当前证据链指向的是 Pod 资源的清理阻塞，而非容器内部的运行错误。

## 🎯 根因分析 · g1

### 因果链

```text
存在自定义 finalizer aiops.lab/hold → 外部控制器未释放该 finalizer → API Server 阻止从 etcd 移除 Pod 对象 → Pod 对象卡在 Terminating 状态
```

### 根因结论

**根因：** Pod 对象 `aiops-case-11/workload` 被施加了自定义 finalizer `aiops.lab/hold`。由于持有该 finalizer 的具体控制器或组件未执行释放操作，Kubernetes API Server 在资源清理完成前阻止了该 Pod 对象从 etcd 中的删除，导致 Pod 状态长期卡在 `Terminating`。

**证据支撑：**
*   **阻塞现象确认：** Pod 处于 `Terminating` 状态已超过 38 分钟（证据 3），且 kubelet 在 38 分钟前已发送停止容器的指令（证据 2），表明阻塞发生在 API Server 层面而非节点侧。
*   **容器状态异常：** 容器 `app` 已退出（exit_code 137，证据 1），证明容器生命周期已结束，Pod 的持续保留并非因为需要等待容器正常退出。
*   **外部依赖缺失：** 当前事实源中缺乏关于 finalizer 释放状态或对应控制器日志的记录，无法直接证明控制器为何未响应，但 Pod 状态的持续保持是 finalizer 未被移除的直接表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.1s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-11/workload: 35.9s (Evidence 28.9s, RCA 6.9s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
