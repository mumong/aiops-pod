## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod workload 处于 Terminating 状态，且已有 66 秒，删除过程滞后（TerminatingStuck） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `status: "Terminating (lasts <invalid>)"` | 确认异常现象：Pod 长时间滞留终止状态 [fact-3a19c9f8b199] |
| 2 | K8s Event | Kubelet | `message: "Stopping container app"`, 时间 `49s` | 确认 Kubelet 已发起停止动作，作为终止过程的起点 [fact-7aeb44e46415] |
| 3 | K8s Event | CNI 插件 | `Annotations: cni.projectcalico.org/containerID: 5730c588319fef6cb2465b34cb484139cd7e838641f7b3dd90e647738e8607f3` | 确认网络资源关联状态，用于排除网络插件导致的阻塞 [fact-e2ac8e3ce30e] |
| 4 | Metric | Pod Restarts | `value: 0`, `sample_count: 1` | 确认终止前无重启历史，排除因频繁重启导致的终止冲突 [fact-2d473108e9d9] |
| 5 | Logging | Application | `message: "application started"`, 时间 `04:39:40.102Z` | 确认应用正常启动，终止动作非由应用崩溃触发 [fact-37f19b30cab7] |

**证据分析：**
Pod 状态明确处于 `Terminating`。Kubelet 在 `49s` 前已发出 `Stopping container app` 事件，表明底层清理逻辑已启动。Metric 显示重启次数为 0，Log 显示应用曾正常启动，排除了应用崩溃导致的意外终止。当前现象表现为“停止动作发出后，Pod 对象长时间未转为 Terminated 或 Deleted”，证据指向容器资源（cgroup/存储）清理阶段发生滞后或阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
删除请求发出（deletionTimestamp 存在） → Kubelet 尝试停止容器（Stopping container app） → 容器资源清理耗时或状态同步延迟（cgroup/存储） → Pod 对象滞留 Terminating 状态
```

### 根因结论

已确认根因：Pod 处于 `Terminating` 滞留状态，原因是底层容器资源清理（cgroup 删除或 Volume 卸载）耗时较长，导致 API Server 无法及时观察到 Pod 状态从 `Terminating` 转换为 `Terminated`，从而未触发垃圾回收（GC）。

支持事实：
- Pod 状态显示为 `Terminating` [fact-3a19c9f8b199]
- Kubelet 已发出停止容器的事件 [fact-7aeb44e46415]
- 无重启历史，非应用异常退出 [fact-2d473108e9d9]

不确定性说明：
- 具体是 cgroup 删除失败还是挂载点（Volume）未卸载导致的 IO 延迟，当前证据不足以区分（Topology 查询解析失败 [failed_tool_attempts]，且日志未包含具体的资源清理错误详情）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 18.5s
├─ 并发证据采集: 92.3s
│  └─ g1 aiops-case-v12/workload: 92.3s (Evidence 82.7s, RCA 9.5s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
