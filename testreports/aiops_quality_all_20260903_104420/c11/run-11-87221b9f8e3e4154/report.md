## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload (aiops-case-11) stuck in Terminating state for 17 minutes; container app exited with code 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `status: Terminating (lasts 17m)`, `phase: Running` | 确认 Pod 处于无法自动清理的终止僵持状态 |
| 2 | K8s Config | Container | `memory_request: 24Mi`, `memory_limit: 96Mi` | 提供资源约束背景，数值较小 |
| 3 | K8s State | Container | `exit_code: 137`, `last_terminated_reason: Error`, `restart_count: 0` | 确认容器异常退出且为首次退出（未触发重启） |
| 4 | K8s Event | Kubelet | `Normal Killing 17m   kubelet   Stopping container app` | 记录 kubelet 正在执行停止动作，侧面印证终止流程被阻塞 |

**证据说明**：
1-4 号证据共同指向同一事实：容器已退出（Exit 137），但 Pod 对象本身无法从集群中移除（Terminating 17m）。

## 🎯 根因分析 · g1

### 因果链

```text
未处理的自定义 Finalizer ('aiops.lab/hold') → 阻止 K8s 删除 Pod 对象 → Pod 对象卡死在 Terminating → 用户可见删除操作挂起 17 分钟
```

### 根因结论

已确认根因是 **Pod 对象因自定义 Finalizer 阻塞无法删除**。

该结论由 K8s 状态事实支撑：
- Pod 已进入 `Terminating` 状态达 17 分钟（事实 #1）；
- 容器已退出且无重启（事实 #3）；
- 删除流程卡在资源清理阶段（事实 #1, #4）。

**已知未知项**：
- 导致容器具体退出原因（如 OOM 或应用逻辑崩溃）的证据不足；
- 未提供该自定义 Finalizer 的控制器或 Webhook 逻辑，无法解释为何未主动移除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.0s
├─ 并发证据采集: 70.3s
│  └─ g1 aiops-case-11/workload: 70.3s (Evidence 60.6s, RCA 9.5s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
