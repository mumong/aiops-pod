## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 容器环境变量引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，导致容器配置注入失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `aiops-case-04/workload-6584f97c76-7ds5p` | 容器 `app` 状态：`Waiting`，原因 `CreateContainerConfigError` | 核心异常标识，锁定容器配置阶段错误 |
| 2 | K8s State | `aiops-case-04/workload-6584f97c76-7ds5p` | 错误详情：`couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供确切的失败原因（引用缺失的 Key） |
| 3 | K8s Event | `kubelet` 日志 | `Failed`: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (32m内出现12次) | 重复确认注入失败的具体细节，非偶发事件 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"}` 当前值为 `1` | 外部指标与内部状态一致，确认为当前活跃异常 |

**证据印证说明：**
Kubernetes 的状态（#1）、错误消息（#2）与 kubelet 事件（#3）在错误细节上完全一致，均指向 Secret `aiops-case-04/workload-input` 中缺少 `unavailable-key`。Metric 指标（#4）独立验证了这一特定的等待原因为 `CreateContainerConfigError`，确认了异常的持续性和确定性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 Secret Key → 容器配置注入阶段 Kubelet 失败 → 容器无法启动 (Waiting) → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因：** 异常的直接根因是 Pod 的容器配置中引用了 `Secret aiops-case-04/workload-input` 中不存在的 key `unavailable-key`。

**分析说明：**
Kubernetes 组件（kubelet）在尝试挂载环境变量时无法解析该 key，导致触发 `CreateContainerConfigError`（证据 #2, #3, #4）。此配置层面的错误直接阻止了容器的启动，从而导致 Pod 停留在 `Pending` 阶段。现有的 K8s 状态与事件记录已充分覆盖该配置错误，无需额外的 Metrics 或 Tracing 数据即可确认根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.0s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 43.3s (Evidence 38.5s, RCA 4.6s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
