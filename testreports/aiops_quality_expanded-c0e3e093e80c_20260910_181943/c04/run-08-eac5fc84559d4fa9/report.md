## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod spec 引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，导致容器配置注入失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接证实 Secret Key 缺失导致容器配置注入失败 |
| 2 | K8s State | kubernetes | `Pending` | 确认 Pod 当前处于未就绪状态 |
| 3 | K8s Config | kubernetes | `app` 容器资源请求/限制：CPU `5m`/`50m`，Memory `8Mi`/`32Mi` | 排除资源不足导致调度失败的可能 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 验证 K8s 事件中的错误类型（配置错误等待中） |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` | 证实容器尚未成功启动，排除重启风暴 |

K8s Event 明确指出了导致失败的具体配置项（缺失的 Secret Key），Metric 数据从侧面确认了该 Pod 正处于因配置错误导致的等待状态，且由于启动失败，重启次数保持为 0，各项指标相互印证，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了不存在的 Secret Key `unavailable-key` → Kubelet 配置注入失败 → 容器无法启动 (CreateContainerConfigError) → Pod 状态卡在 Pending
```

### 根因结论

已确认的根因为：Pod 规范中引用的 Secret `aiops-case-04/workload-input` 中不存在 `unavailable-key` 这个 key。

该配置错误导致 kubelet 在尝试挂载环境变量或卷时无法找到对应键值，从而抛出 `CreateContainerConfigError`，使容器无法进入运行状态，直接引发 Pod 处于 Pending 状态且无法被用户访问。此结论直接由事实 #1 (Event) 支持，且与事实 #4 (Metric) 中观测到的配置错误等待状态完全一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 24.7s
├─ 并发证据采集: 28.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 28.5s (Evidence 24.2s, RCA 4.1s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
