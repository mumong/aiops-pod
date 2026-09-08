## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod template 错误地引用了 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubelet | `waiting_reason: CreateContainerConfigError` (Container: `app`) | **直接现象**：Pod 无法启动，进入配置加载失败状态 [fact-5cd7770d7d9a] |
| 2 | K8s State | Kubelet | `waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | **核心归因**：明确指明缺少特定 Secret key 导致 [fact-b43341c56cf8] |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | **状态确认**：Prometheus 指标侧确认容器处于 `CreateContainerConfigError` 等待状态 [fact-225164fd6523] |
| 4 | Topology | K8s API | `pod.phase: Pending` | **阶段限制**：Pod 停留在 Pending 阶段，说明尚未达到调度完成后的运行期，日志/Tracing 缺失属于物理预期 [fact-72be8fbcc73c] |

**证据互证分析**：
Kubelet 的报错信息（#1, #2）与 Prometheus 的等待原因指标（#3）在根因和状态上完全一致。`Pending` 状态（#4）解释了为何无法采集到应用层面的日志或链路追踪数据，排除了因网络或探针故障导致的空数据可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 错误引用不存在的 Secret key 'unavailable-key' 
→ Kubelet 在拉取 Secret 挂载项时未找到目标 key
→ 容器启动阶段被阻断，进入 CreateContainerConfigError 状态
→ Pod 卡在 Pending 状态，应用不可用
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的配置模板中存在引用错误。Pod 试图挂载 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 key 在 Secret 中实际并不存在。这一配置错误直接导致容器无法完成初始化挂载，从而引发了 `CreateContainerConfigError` 状态 [fact-b43341c56cf8]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 21.5s
├─ 并发证据采集: 62.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 62.9s (Evidence 55.9s, RCA 6.9s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
