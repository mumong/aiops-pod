## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态，容器 app 无法启动，已等待 92 分钟。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-14f7328597d3` | `Normal Pulled 117s (x422 over 92m)` 容器镜像 `xnet.registry.io:8443/observability/python:3-alpine` 已成功拉取 | 排除镜像拉取失败，容器无法启动发生在配置阶段 |
| 2 | K8s State | `fact-ad333081d951` | `container.app.message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指明容器启动配置阶段的具体错误原因 |
| 3 | K8s State | `fact-e3ac8b8d2baa` | `container.app.reason`: `CreateContainerConfigError` | 确认异常状态类型为配置创建错误 |
| 4 | Metric | `fact-7d0c4ff575f9` | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1 | 独立确认容器处于配置错误的等待状态 |
| 5 | K8s State | `fact-800e0d8b9f80` | `pod.phase`: `Pending` | 确认 Pod 始终未进入 Running 状态 |

**证据说明：**
- 证据 #1 表明网络与镜像下载正常，故障点位于容器创建前的配置加载环节。
- 证据 #2 与 #3 结合，将异常状态精确映射到 Secret 中特定键 `unavailable-key` 的缺失，形成因果闭环。
- 证据 #4 的 Metrics 数据与 K8s 状态一致，独立印证了错误类型。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用 Secret aiops-case-04/workload-input 中的键 unavailable-key → 该键在 Secret 中不存在 → Kubelet 解析环境变量/卷配置失败 → Pod 保持 Pending 且容器报 CreateContainerConfigError 无法启动
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的 YAML 定义中引用了 `Secret aiops-case-04/workload-input` 里的键 `unavailable-key`，但该 Secret 实际数据中不存在此键。这一配置不匹配导致 Kubelet 在初始化容器时抛出 `CreateContainerConfigError`（证据 #2, #3），直接表现为 Pod 长期处于 Pending 状态（证据 #5）且容器处于等待状态（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 18.0s
├─ 并发证据采集: 84.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 84.5s (Evidence 76.2s, RCA 8.2s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
