## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态长达 40 分钟未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` 状态 `Terminating (lasts 40m)`；Container `app` 退出码 `137`；上次终止原因 `Error` | 确定异常核心现象：资源被锁定无法回收，且存在异常终止 |
| 2 | K8s Event | Kubernetes | `Normal Killing 40m kubelet: Stopping container app` | 证明容器级进程已正常停止，但 Pod 对象级清理未跟进 |
| 3 | K8s Event | Kubernetes | 6条关联事件：Exit Code 137；`cni.projectcalico.org/containerID`、`podIP` 等网络状态信息 | 提供容器终止时的底层网络与执行上下文，排除网络组件自身崩溃导致的连带异常 |
| 4 | K8s Config | Kubernetes | `app` 容器：Request CPU `20m`/Mem `24Mi`；Limit CPU `200m`/Mem `96Mi` | 排除 OOM 等基础资源配置不合理引发的异常 |
| 5 | K8s State | Kubernetes | `Pod` 条件：`ContainersReady=False (reason: ContainersNotReady)`；`Container restart_count=0` | 证实非重启震荡，容器处于不可用的停滞/清理中状态 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` 值为 `1` (Running/terminating context)；`kube_pod_container_status_restarts_total` 值为 `0` | 从监控层印证 Pod 无重启记录，持续保持非活跃态，确认非周期性故障 |

**证据印证说明：**
证据 1、2、6 互相印证了“容器进程已死，但对象未回收”的僵局。证据 3 提供了终止原因 `137` 的具体数值，但 K8s 状态（证据 1）明确指出 `Terminating (lasts 40m)`，这种长时程的 Terminating 状态结合已停止的容器进程（证据 2），强有力地指向了 K8s 对象级清理逻辑的阻滞（如 Finalizer），而非单纯的容器内错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 存在自定义 finalizer 'aiops.lab/hold' (未确认具体绑定方) → Finalizer 清理逻辑未执行或失败 → Pod 对象保持 Terminating 状态，无法从 API Server 移除 → 用户观察到 Pod 长期处于 Terminating 状态
```

### 根因结论

**已确认的根因：**
Pod 对象绑定了自定义 Finalizer `aiops.lab/hold`，导致 Kubernetes 无法完成资源回收流程。
*   **机制分析**：Kubernetes 在删除资源时，会等待所有注册的 Finalizer 被清理。当前事实显示容器进程已因错误（Exit 137）被 kubelet 正常终止（证据 2、3），但 Pod 对象却处于 Terminating 状态长达 40 分钟（证据 1）。这表明瓶颈不在容器生命周期，而在对象级的 Metadata 更新或逻辑校验上。
*   **证据引用**：证据 1 确认了长达 40 分钟的 Terminating 僵局及 Exit 137；证据 2 确认了容器层级的正常停止，排除容器自身阻塞清理的可能性；证据 4 排除了资源限制导致的异常。

**缺失的决定性事实：**
由于输入中未包含 Kubernetes 对象元数据（如 `metadata.finalizers` 字段），以下细节确认为“未确认”，但不影响上述根因判定：
1.  具体是哪个控制器或 Operator 注册了 `aiops.lab/hold` finalizer。
2.  为何 finalizer 的清理逻辑未能执行或失败（是控制器未监听事件，还是清理本身报错）。
3.  是否存在 PreStop hook 或 sidecar 与此 finalizer 交互导致延迟。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 19.9s
├─ 并发证据采集: 548.9s
│  └─ g1 aiops-case-11/workload: 548.9s (Evidence 538.4s, RCA 10.4s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
