## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 处于 ContainerCreating 状态，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=1, reason="ContainerCreating" | 直接确认容器处于因等待资源或镜像导致停滞的状态 |
| 2 | Metric | prometheus | `kube_pod_status_phase`=1, phase="Pending" | 确认 Pod 未成功进入 Running 阶段 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total`=0 | 排除重启风暴或已启动后崩溃的可能性 |

当前证据主要依赖 Metric 维度，Logging 和 Tracing 维度因容器未启动无法获取直接证据。Metric 数据与正式 RCA 的因果链在“容器未能进入运行状态”这一结论上相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 未配置 imagePullSecrets 且镜像为公开仓库 → 镜像仓库返回 Basic challenge 认证失败 → Kubelet 执行 pull 失败并触发 ImagePullBackOff → Pod 维持在 ContainerCreating 状态
```

### 根因结论

已确认根因为镜像拉取认证失败（unauthorized），直接原因是 Pod 未配置 `imagePullSecrets`（证据：`fact-ca3e7dea0def`、`fact-54ee551791c0`）。现有证据已支持上述结论的发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 25.2s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 46.7s (Evidence 40.1s, RCA 6.5s)
└─ 汇总总结: 4.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed
