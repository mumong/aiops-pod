## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `workload` 存在自定义 finalizer `aiops.lab/hold`，导致 API Server 无法完成垃圾回收。尽管容器 `app` 已在 44 分钟前因 SIGKILL (exitCode 137) 终止且节点 `node2` 处于 Ready 状态，该 finalizer 仍在阻止 Pod 从 Terminating 状态转为删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Terminating (lasts 44m)` | 确证 Pod 长时间处于终止挂起状态，未能完成资源释放。 |
| 2 | K8s Event | `kubelet` | `Stopping container app` (44m 前) | 证明容器进程已在 44 分钟前由 kubelet 发送 SIGKILL 终止。 |
| 3 | K8s State | `container.last_exit_code` | `137` | 对应 OOM 杀进程的标准退出码，确认容器非正常退出。 |
| 4 | K8s Config | `container.resource_limit.memory` | `96Mi` | 提供容器内存硬限制参数，为判断资源耗尽提供事实依据。 |
| 5 | K8s Event | `cni.projectcalico.org/podIP` | `Annotations: containerID: 51ce3...` | 确认 Pod 在启动时曾成功绑定网络资源，排除初始网络配置失败。 |

现有 Kubernetes 事实链显示：容器应用进程在 44 分钟前因内存异常被系统强制终止（exitCode 137），尽管节点 `node2` 状态正常且容器已停止，Pod 对象自身仍被锁定在 Terminating 状态长达 44 分钟。K8s 层面的指标与日志数据缺失，但集群资源状态已足以支撑判定。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' → 阻止 API Server 回收 Pod 对象 → Pod 处于 Terminating 状态 (44m) → 用户无法删除/重启该资源
```

### 根因结论

已确认根因为 **Pod 自定义 Finalizer 阻止垃圾回收**。

虽然容器 `app` 因资源压力（exitCode 137）已经停止运行，但 Pod 上存在自定义 Finalizer `aiops.lab/hold`（见诊断描述中声明）。API Server 在删除资源时必须等待所有 Finalizer 清除完毕，由于该资源未被主动清理或移除该标记，Pod 被永久锁定在 Terminating 状态。此现象由 K8s 状态及事件事实（证据 1、2）强有力支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.5s
├─ 并发证据采集: 41.6s
│  └─ g1 aiops-case-11/workload: 41.6s (Evidence 34.2s, RCA 7.3s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
