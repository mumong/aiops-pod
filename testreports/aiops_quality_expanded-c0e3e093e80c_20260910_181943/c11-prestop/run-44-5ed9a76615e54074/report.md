## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'message': 'Annotations:               cni.projectcalico.org/containerID: 452fcde91bd677670f03e0437a9e28988cdb9a593d4579fb44710c72f4c213a1'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 重启计数为 0；Pod 处于 Terminating 状态 | 证明容器在生命周期内无异常崩溃重启，终止非由健康检查失败触发 |
| 2 | K8s State | Kubernetes | Pod 处于 `Running` 阶段 | 确认 Pod 资源仍活跃，终止流程尚未最终清理资源 |
| 3 | K8s Event | Kubernetes | `Normal Killing`, 51s前, `Stopping container app` | 确认控制面已发出终止指令，Kubelet 已介入开始停止流程 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 0 | 佐证无应用内部进程崩溃导致的重启行为 |
| 5 | Logging | Elasticsearch | `application started` (2026-09-14T06:09:17.703Z) | 确认应用已正常启动，但日志无终止或错误迹象 |

**证据说明：**
K8s 事件与状态确认删除指令已送达且被 Kubelet 响应（证据 2、3、4），但应用日志仅显示正常启动（证据 5）且重启计数为 0（证据 1）。所有维度均指向“应用仍在运行中未退出”，但未提供应用退出被阻塞的底层日志（如 PreStop 钩子执行情况），属于现象一致但机制未明示。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：Pod 被触发删除（deletionTimestamp 存在） → 失败机制：应用进程持续阻塞等待 /state/teardown-requested 文件出现（未确认文件是否存在及是否写入） → 直接失败：容器拒绝退出直至 Grace Period (3900s) 超时 → 用户可见现象：Pod 长期处于 Terminating 状态
```

### 根因结论

现有证据**不足**发布正式 RCA。虽然现象明确符合“等待外部信号文件”导致的终止卡死特征，但缺少以下关键事实以区分是“正常等待”还是“异常故障”：
1. 信号文件 `/state/teardown-requested` 的实际存在状态；
2. PreStop Hook 的具体执行上下文及是否正在运行；
3. 发起删除的控制器或外部源是否完成了文件写入操作。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.1s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-v12/workload: 42.6s (Evidence 29.6s, RCA 12.9s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
