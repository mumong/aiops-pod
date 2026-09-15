## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 因 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: app 容器处于 `CreateContainerConfigError` | 确认异常直接原因：容器配置注入失败导致无法启动 |
| 2 | K8s Event | kubernetes | `Failed` Event: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 提供直接证据：Pod spec 引用了不存在的 ConfigMap key，是配置失败的根源 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (`reason=CreateContainerConfigError`): 当前值 `1`，无趋势数据 | 验证异常状态持续存在 |
| 4 | K8s State | kubernetes | `pod.status`: `Pending`；`container.restart_count`: `0` | 确认异常发生在启动阶段，容器因配置错误从未进入运行状态，故无重启或日志 |

**证据印证：**
K8s Event（#2）揭示了具体的配置缺失，直接导致了 `CreateContainerConfigError`（#1）和 Pod 长期 Pending（#4）的状态，Metric 数据（#3）独立确认了这一状态的当前存在。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap aiops-case-v11/workload-input 缺少 key unavailable-key → Pod spec 引用该不存在的 key 进行配置注入 → kubelet 无法完成容器创建 → Pod 处于 Pending 状态，容器进入 CreateContainerConfigError 等待状态
```

### 根因结论
已确认的根因是 Pod 定义中错误地引用了 `ConfigMap aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`。
这一配置错误导致 kubelet 在尝试启动容器时因无法注入配置而直接报错，致使 Pod 始终停留在 `Pending` 状态，无法进入运行或重启循环。证据链完整，无需进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.7s
├─ 并发证据采集: 43.8s
│  └─ g1 aiops-case-v11/workload: 43.8s (Evidence 35.7s, RCA 8.1s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
