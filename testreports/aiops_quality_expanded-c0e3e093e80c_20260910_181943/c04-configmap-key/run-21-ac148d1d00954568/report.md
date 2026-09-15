## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的容器配置引用了 ConfigMap 'aiops-case-v11/workload-input' 中不存在的 key 'unavailable-key'，导致容器创建失败，异常持续未恢复。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase` = Pending, `pod.status` = Pending | 确认实体当前处于非运行状态 |
| 2 | K8s Event | Kubernetes | `Failed`: `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (39m, x12) | 提供导致失败的确定性错误日志 |
| 3 | K8s Config | Kubernetes | `container.resource_request.cpu`: 5m, `resource_limit.cpu`: 50m, `memory`: 32Mi | 资源限制配置正常，排除资源不足导致的调度失败 |

表格后用 1-3 条简短文字说明证据如何互相印证或冲突；只能引用表中实际展示的证据编号和维度，跨维度 trace_id 关联存在时必须写出。
Kubernetes 事件日志（#2）明确指出了配置缺失的原因，与容器状态（#1）中的 Pending 和配置错误信息高度一致。资源配置（#3）显示请求与限制均已正确定义，证实故障并非由资源竞争引起。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 缺失键 'unavailable-key' → 容器配置校验失败 (CreateContainerConfigError) → Pod 状态卡在 Pending → 容器创建持续失败
```

### 根因结论

已确认的根因为 `Pod aiops-case-v11/workload` 的容器配置引用了 ConfigMap `'aiops-case-v11/workload-input'` 中不存在的 key `'unavailable-key'`。该配置错误导致 kubelet 无法完成容器启动，异常状态（Pending / CreateContainerConfigError）持续未恢复（证据 #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 54.3s
├─ 问题定位: 15.5s
├─ 并发证据采集: 32.5s
│  └─ g1 aiops-case-v11/workload: 32.5s (Evidence 26.8s, RCA 5.6s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
