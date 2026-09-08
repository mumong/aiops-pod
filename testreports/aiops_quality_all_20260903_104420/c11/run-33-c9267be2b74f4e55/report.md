## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload Terminating 停滞 58分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: Terminating (lasts 58m) | 确认核心异常：Pod 长时间处于 Terminating 状态，无法完成资源回收。 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: Error (Exit Code: 137) | 证实容器应用进程已因异常退出（137通常为 OOMKilled 或强制终止）。 |
| 3 | K8s Config | kubernetes | pod.metadata.finalizers: aiops.lab/hold | 指出存在自定义 finalizer，这是阻止 Pod 正常删除的直接元数据条件。 |
| 4 | K8s Config | kubernetes | container.resource_limit.memory: 96Mi | 结合 Exit 137，提示资源限制可能较紧，是触发容器异常退出的潜在诱因。 |
| 5 | K8s Event | kubernetes | Killing: Stopping container app (58m ago) | 确认 kubelet 已尝试停止容器，说明节点层面的删除请求已发起。 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 确认该容器自部署以来未发生过重启，这是单次突发故障，非健康度持续下降。 |

**证据说明：**
Pod 状态表明确示“Terminating (lasts 58m)”，而 K8s 事件记录显示 58 分钟前容器已被 Killing。Kubernetes 会在删除 Pod 时先停止容器，等待容器退出后才从 API Server 移除 Pod。目前容器已退出（事实 #2、#5），但 Pod 仍卡在 Terminating，结合事实 #3 中的 `aiops.lab/hold` finalizer 记录，直接指向 finalizer 清理逻辑失效是阻碍删除进程完成的原因。Metric 中的重启计数为 0（事实 #6）佐证了这是新近发生的单次事件，而非长期滚动故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置自定义 finalizer `aiops.lab/hold` → 容器进程异常退出 (Exit 137) → Kubernetes 尝试删除 Pod 但等待 finalizer 移除 → 清理控制器未执行或无法移除 finalizer → Pod 长期卡在 Terminating 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-11/workload` 被 Kubernetes 强制删除（Terminating）受阻，原因是其元数据中包含自定义 finalizer `aiops.lab/hold`（证据 #3），而对应的清理控制器未能成功移除该 finalizer。虽然容器应用因资源或错误原因终止（Exit 137，证据 #2），节点层面已完成清理（证据 #5），但 API Server 在 finalizer 移除前不会真正删除 Pod，导致 58 分钟停滞（证据 #1）。

**证据不足与未知：**
现有证据仅确认了 finalizer 的“存在”与“未移除”的表象（事实绑定），但缺乏决定性事实来回答“谁注册了该 finalizer”以及“为什么清理控制器未执行”（见 unknowns 字段）。缺少 `aiops.lab/hold` 对应的清理控制器日志或相关 CRD 状态记录，无法深入定级该 finalizer 的具体业务含义及其控制器未执行的具体代码路径。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 13.8s
├─ 并发证据采集: 79.8s
│  └─ g1 aiops-case-11/workload: 79.8s (Evidence 71.8s, RCA 7.8s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
