## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 处于 Waiting 状态且原因为 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.app` 处于 `Waiting` 状态，原因为 `CreateContainerConfigError`，提示 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` [fact-bb2f4c71500f, fact-bc96c5c308a6] | 直接证明启动失败的原因为配置缺失 |
| 2 | K8s State | Kubernetes | Pod 状态为 `Pending`，`ContainersReady` 和 `Ready` 均为 `False`，原因 `ContainersNotReady` [fact-814ad3654287, fact-39a04de2115e, fact-5f093abaaea7] | 确认 Pod 无法进入运行状态，处于初始化阻塞阶段 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (reason: `CreateContainerConfigError`)，`restart_count` 为 `0` [fact-333eec3daf62, fact-6b0e04eeaa2e] | 确认处于等待状态，且零重启证明容器根本未成功拉取启动 |

证据 1 的 Kubernetes 错误消息精确指向了缺少的 Secret Key，与证据 3 中等待原因指标一致。证据 2 的容器就绪状态表明 Pod 调度成功但因配置未就绪而卡在等待阶段。

## 🎯 根因分析 · g1

### 因果链
```text
Secret aiops-case-04/workload-input 缺少 key unavailable-key → 容器启动时环境配置失败 → 状态转变为 CreateContainerConfigError → Pod 保持 Pending 状态
```

### 根因结论
已确认根因为：Pod 定义中引用的 Secret `aiops-case-04/workload-input` 中缺失 key `unavailable-key`，导致 kubelet 无法完成容器配置并启动容器。
该结论由证据 1 中 K8s 事件返回的具体错误信息直接证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.5s
├─ 并发证据采集: 35.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 35.0s (Evidence 28.4s, RCA 6.5s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
