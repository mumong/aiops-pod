## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | {'message': 'Annotations:      cni.projectcalico.org/containerID: e9690566e91643d819af00d79b4df84b56ae09d0c62c7f441254b7d5523bf6b5'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `status: Pending`, `container restart_count: 0` | 确立 Pod 当前挂起状态，且应用容器尚未进入运行周期 |
| 2 | K8s Event | Kubernetes | `Annotations: cni.projectcalico.org/containerID: e9690566e91643d819af00d79b4df84b56ae09d0c62c7f441254b7d5523bf6b5` | 存在 CNI 相关的网络注解记录，但未发现引发 `CreateContainerConfigError` 的 `Warning` 事件或具体配置失败原因 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 指标层确证容器卡在配置错误阶段，与 K8s 状态的 `Waiting` 状态一致 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.cpu: 50m`, `container.resource_request.cpu: 5m` (其他资源同理) | 提供资源配额上下文，资源限制与请求设置均属于极小值范围 |

**证据说明**：
K8s 事件记录显示存在 CNI 注解信息但缺乏导致创建失败的 `Warning` 消息；Prometheus 指标明确将挂起原因标识为 `CreateContainerConfigError`。由于容器状态始终为 `Pending` 且 `restart_count` 为 0，日志与链路追踪被确认为物理不可达。现有证据足以确认故障现象，但未能通过事件或指标定位导致配置错误的具体底层原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 处于 Pending 状态 → 容器 app 处于 Waiting 状态，原因 CreateContainerConfigError → Kubernetes 事件未记录导致配置错误的 Warning 消息 → 缺少节点侧 kubelet 日志，无法查明底层失败机制
```

### 根因结论

**证据不足**。

现有事实确认 `app` 容器因配置错误（`CreateContainerConfigError`）处于等待状态，但缺乏决定性的故障根源证据：
1.  **K8s 事件缺失关键信息**：未捕获到具体的 `Warning` 事件来指出是 Secret 挂载失败、ConfigMap 引用错误还是其他配置项问题。
2.  **底层日志不可达**：由于容器从未成功启动，`elasticsearch` 无应用日志，`deepflow` 和 `tempo` 无业务 Trace，且未采集到节点侧 `kubelet` 日志来揭示容器运行时创建失败的具体错误原因。

缺少节点侧诊断数据或更详细的 K8s 事件记录以确认具体的配置失效点。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 24.2s
├─ 并发证据采集: 553.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 553.2s (Evidence 546.0s, RCA 7.0s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
