## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | aiops-case-v11/workload Pod处于Pending状态，容器处于Waiting且Reason为CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | 状态：Pending | 证实 Pod 当前停留在调度等待阶段，未进入运行状态。 |
| 2 | K8s Event | K8s Event Message | `Warning Failed 45m (x12 over 47m) kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接指出容器创建阶段报错的具体原因，是定位配置缺失的确定性证据。 |
| 3 | Metric | Prometheus (`kube_pod_container_status_waiting_reason`) | 1 (reason: `CreateContainerConfigError`) | 从监控指标确认了容器的具体等待原因为配置加载失败，排除了其他原因（如镜像拉取失败）。 |
| 4 | K8s Config | K8s Config | container.app.cpu 请求: 5m, 限制: 50m; memory 请求: 8Mi, 限制: 32Mi | 提供资源边界信息，排除因资源超额导致调度失败的可能性（非调度维度的根因）。 |

**证据说明**：
K8s 事件（#2）详细记录了容器创建期间 `kubelet` 报错找不到特定 Key 的事实，该事实与 Prometheus 监控指标（#3）中反映的 `CreateContainerConfigError` 等待原因完美互证。K8s 状态（#1）和 Metrics（#4）共同锁定了故障的宏观表现（Pending）和微观原因（配置缺失），排除了其他资源或网络问题。由于 Pod 未启动，Logging 和 Tracing 维度无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec中引用了ConfigMap 'aiops-case-v11/workload-input'中不存在的Key 'unavailable-key' → kubelet尝试挂载配置查找Key失败 → 容器初始化阶段报错并进入Waiting状态 → Pod整体状态停留在Pending，无法对外提供服务
```

### 根因结论

已确认的根因是：**Pod 规格（Pod spec）错误引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 Key `unavailable-key`**。

该事实由 K8s Event（#2）提供的原始错误信息直接支撑，并由 Metrics（#3）确认了由此产生的 `CreateContainerConfigError` 状态。配置引用不匹配导致 kubelet 在初始化阶段无法加载所需配置，进而阻断了容器的创建流程。

---

## 📊 性能统计

```text
├─ 总耗时: 46.8s
├─ 问题定位: 11.6s
├─ 并发证据采集: 26.7s
│  └─ g1 aiops-case-v11/workload: 26.7s (Evidence 19.3s, RCA 7.3s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
