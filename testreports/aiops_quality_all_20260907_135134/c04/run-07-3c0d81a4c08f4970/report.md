## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 配置引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'，导致 kubelet 无法注入环境变量，容器配置失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: app 容器处于 `CreateContainerConfigError` 状态 | 定位故障机制为配置阶段阻断，非运行时异常 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出导致配置失败的具体缺失资源键 |
| 3 | K8s Event | Kubernetes | `Failed` 事件：`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (12次) | 确认 kubelet 在执行容器配置时持续因上述错误而失败 |
| 4 | K8s State | Kubernetes | `pod.phase`: `Pending`；`ContainersNotReady`: `containers with unready status: [app]` | 验证 Pod 整体处于阻塞状态，未进入运行期 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (原因 `CreateContainerConfigError`) | 从指标侧印证 Kubernetes 状态中描述的等待原因 |

**证据说明：**
Kubernetes 状态事实与事件事实（#2、#3）精确一致，共同指向同一个具体的 Secret key 缺失问题；指标事实（#5）与容器等待状态（#1）相互印证，排除了时序差异导致的误报。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Secret 中不存在的 key → kubelet 无法注入环境变量 → CreateContainerConfigError → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为：Pod 定义中引用了 `aiops-case-04/workload-input` Secret 中的 `unavailable-key` 键，但该键实际不存在（证据 #2, #3, #5）。该配置缺失导致 kubelet 无法完成环境变量的注入，从而将容器状态维持在 `CreateContainerConfigError`，使 Pod 无法就绪。现有证据已充分闭环，无需进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.6s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 39.2s (Evidence 33.6s, RCA 5.5s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
