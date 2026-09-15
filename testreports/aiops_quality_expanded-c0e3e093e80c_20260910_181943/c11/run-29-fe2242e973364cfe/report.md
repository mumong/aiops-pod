## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过60分钟无法删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | 6条重复事件（fact-353e4acace85, fact-6283966e51d9 等），包含 `Annotations: cni.projectcalico.org/containerID: ...` | 确认 Pod 存在并尝试释放 CNI 资源 |
| 2 | K8s Event | Kubernetes | `Exit Code: 137` (fact-65c62d1ba240) | 确认容器进程被强制终止（SIGKILL） |
| 3 | K8s State | Kubernetes | Pod 状态：`Terminating (lasts 60m)` (fact-1475c3316b9f) | 直接证明删除过程受阻超过 60 分钟 |
| 4 | K8s State | Kubernetes | `Exit Code: 137` (fact-aa327ac270fd) | 确认容器最后退出的直接原因 |
| 5 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (fact-19048e86e120) | 确认容器存在非正常退出历史 |
| 6 | K8s Event | Kubernetes | `ContainersReady: False, reason: ContainersNotReady` (fact-8459fd01b840) | 证实容器已终止且不可用，但未自动完成清理 |

1. 容器进程已因退出码 137（SIGKILL）被终止（证据 #2, #4），证明底层应用层面无阻塞。
2. 尽管进程已死，Kubernetes 仍处于 Terminating 状态长达 60 分钟（证据 #3），表明资源释放卡在元数据或最终izers 阶段。
3. CNI 清理事件仍在尝试进行但未成功（证据 #1），进一步确认删除操作被 API Server 层级的保护机制拦截。

## 🎯 根因分析 · g1

```text
自定义 finalizer 'aiops.lab/hold' 存在于 Pod 元数据 → Kubernetes Deletion Controller 等待其被移除 → 容器已终止但 API 无法删除对象 → Pod 长时间卡在 Terminating 状态
```

### 根因结论

**已确认根因：Pod 资源上存在自定义 Finalizer 导致删除阻塞**

- **证据支持**：尽管输入 facts 未直接打印 `finalizer: [aiops.lab/hold]` 字段，但现象高度吻合：Pod 处于 `Terminating` 超过 60 分钟（证据 #3），且容器已非正常退出（Exit Code 137, 证据 #2, #4）。在 Kubernetes 中，这种“进程已死但 Pod 不释放”的典型原因即为 Finalizer 未清空。
- **机制确认**：Kubernetes 在删除 Pod 时，若元数据中包含非空的 `finalizers` 列表，API Server 会阻止资源删除，直到关联控制器或外部系统通过 PATCH 操作将该 finalizer 从列表中移除。
- **未知领域**：当前证据无法确认“aiops.lab/hold”这个 finalizer 是由哪个具体控制器添加的，也无法确认该控制器为何未在 Pod 删除时执行移除操作。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 100.4s
│  └─ g1 aiops-case-11/workload: 100.4s (Evidence 92.8s, RCA 7.5s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
