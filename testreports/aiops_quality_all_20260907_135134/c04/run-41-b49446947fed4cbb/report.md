## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p处于Pending状态，容器app处于CreateContainerConfigError，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Normal Pulled 63m` (x278): Image `xnet.registry.io:8443/observability/python:3-alpine` already present | 排除镜像拉取故障，确认故障点在镜像拉取之后 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `CreateContainerConfigError` | 直接定位到容器配置阶段失败，阻断启动 |
| 3 | K8s State | kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认缺失的具体 Secret Key，指向 Pod 定义与 Secret 内容的不匹配 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 `1` | 验证了 K8s State 中的报错原因在观测窗口内持续存在 |
| 5 | K8s State | kubernetes | `pod.status`: `Pending`; `phase`: `Pending` | 确认为最终停滞状态，容器未完成创建 |
| 6 | K8s State | kubernetes | `container.restart_count`: `0` | 确认该异常导致 Pod 无法初次启动，不存在重试或 CrashLoopBackOff 行为 |

**证据链说明**：
K8s State 中的 `waiting_message` (证据3) 提供了确切的错误细节，指出 Secret `aiops-case-04/workload-input` 中缺少 `unavailable-key`。结合 `Pulled` 事件 (证据1) 证明镜像获取成功，但配置校验阶段受阻。Metric 数据 (证据4) 从时间序列上佐证了这一配置错误状态的持续性。证据间逻辑闭环，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺少 key 'unavailable-key' → 
Pod Spec 引用了该缺失的 key 进行配置注入 → 
kubelet 在创建容器前验证配置失败，触发 CreateContainerConfigError → 
Pod 处于 Pending 状态，容器 app 始终无法运行
```

### 根因结论

**已确认根因**：Pod `workload-6584f97c76-7ds5p` 的配置错误。
Pod 的 Spec 中引用了 `aiops-case-04/workload-input` Secret 中的 `unavailable-key`，但该 Key 实际不存在于该 Secret 中。这一配置不匹配直接导致 `kubelet` 拒绝创建容器，产生 `CreateContainerConfigError`，进而使 Pod 维持在 `Pending` 状态 (证据2, 3, 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.2s
├─ 并发证据采集: 42.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 42.2s (Evidence 35.0s, RCA 7.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
