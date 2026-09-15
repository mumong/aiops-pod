## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | 应用层终止逻辑包含长超时等待且缺失触发信号 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` (fact-837e031191e8) | `Normal Killing ... Stopping container app` (37s) | 确认触发机制：kubelet 已执行终止流程并发出信号 |
| 2 | K8s Config | `container.resource_limit.memory` (fact-02bc9a079e2a) | `32Mi` | 排除容器内存硬限制触发 OOMKilled 导致立即退出的可能性 |
| 3 | K8s State | `pod.status` (fact-f0fe6798e7c4) | `Terminating (lasts <invalid>)` | 确认症状：Pod 陷入终止状态且长时间未释放，处于挂起态 |
| 4 | Logging | `elasticsearch` (fact-ff770fb7f438) | `application started` (2026-09-14T05:56:21.404Z) | 仅确认应用曾启动成功；缺失后续终止阶段的日志以支撑具体的“长超时等待”分析 |
| 5 | K8s Event | `CNI/Annotations` (fact-2133f66a12b8等) | `cni.projectcalico.org/podIP: 172.16.104.9/32` 等 5条 | 排除 CNI 资源分配错误或注解缺失导致的 Pod 初始化/终止失败 |

**证据关联说明：**
证据 1 提供了直接的外部触发证据（Kubelet 发出 Killing），证据 3 展示了异常结果（Pod 挂起）。证据 2 排除了资源限制导致的被动终止。日志证据（证据 4）仅证实了生命周期起点，缺失终止阶段日志，无法单独验证长超时行为，因此终止逻辑的具体表现依赖正式 RCA 的因果链推论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 收到删除请求 (deletionTimestamp已设置) → kubelet 发送 SIGTERM 并执行 lifecycle.preStop hook → preStop hook 启动最长 3600秒 的循环等待 /state/teardown-requested 文件 (未配置强制中断) → 主容器同样循环等待同一文件存在才退出 → 应用层终止逻辑包含长超时等待且缺失触发信号
```

### 根因结论

已确认根因为 **应用层终止逻辑存在长超时等待且缺失触发信号**。

- **机制分析**：Kubelet 在收到 Pod 删除请求后（证据 1），正常发出 `SIGTERM` 并执行 `preStop` 生命周期钩子。
- **失败表现**：Pod 并未在预期的秒级时间窗内退出，而是陷入了 `Terminating` 状态的挂起（证据 3）。正式 RCA 指出，`preStop` 钩子中启动了针对 `/state/teardown-requested` 文件的最长 3600 秒的循环等待。
- **逻辑缺陷**：主容器未配置强制中断机制（如 `SIGTERM` handler 强制退出），而是同样陷入对同一文件存在的等待，导致即使接收到终止信号也无法及时释放资源。
- **支撑情况**：日志证据（证据 4）未提供该等待过程的直接记录，但 K8s 层面的终止状态（证据 3）与触发事件（证据 1）之间的异常延迟，以及排除了资源限制因素（证据 2），共同指向了应用内部逻辑导致的终止延迟。

---

## 📊 性能统计

```text
├─ 总耗时: 58.0s
├─ 问题定位: 17.2s
├─ 并发证据采集: 29.0s
│  └─ g1 aiops-case-v12/workload: 29.0s (Evidence 20.6s, RCA 8.3s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
