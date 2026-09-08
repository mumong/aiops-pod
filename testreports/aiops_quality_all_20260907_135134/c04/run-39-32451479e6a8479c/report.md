## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 处于 Waiting 状态，Reason=CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed 59m (x12 over 61m) kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认为容器配置错误，直接归因于缺失 Secret Key |
| 2 | K8s State | container.waiting_message | `container: app, message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 与 Event 一致，证明容器启动失败的具体技术原因 |
| 3 | K8s State | pod.phase | `Pending` | 确认 Pod 处于挂起状态，未进入运行态 |
| 4 | K8s State | pod.condition | `Ready=False (ContainersNotReady), Initialized=True` | 确认 Pod 初始化成功但因容器未就绪而不可用 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 量化确认容器等待原因为配置错误，与 K8s 事实交叉印证 |

**证据关联说明：**
- **编号 1 & 2**：Kubernetes 事件与容器等待消息完全一致，直接锁定了 `unavailable-key` 缺失是失败原因。
- **编号 1 & 5**：Metric 中的 `reason` 标签与 Event 中的错误类型（`CreateContainerConfigError`）完全匹配，排除了其他类型启动异常的可能性。
- **编号 3 & 4**：状态条件证实了 Pod 已调度并成功初始化，但由于容器配置问题导致 `ContainersNotReady`，符合配置错误的典型表现。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用 Secret key 'unavailable-key' → Secret 'workload-input' 中缺失该 Key → kubelet 注入环境变量失败 → Pod 进入 CreateContainerConfigError 状态
```

### 根因结论
已确认根因：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`（证据 #1, #2, #5）。由于该 Key 缺失，kubelet 在创建容器时无法完成环境变量注入，导致容器处于 `CreateContainerConfigError` 状态并持续重启等待，最终表现为 Pod 处于 `Pending` 且不可用（证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 41.1s (Evidence 31.7s, RCA 9.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
