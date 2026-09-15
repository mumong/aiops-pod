## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 持续处于 Pending/CreateContainerConfigError 状态，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-1515775ba8d0) | `Warning Failed... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接报错原因：Secret Key 缺失 |
| 2 | K8s State | kubernetes (fact-b59cea574594) | `Waiting: message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 证实容器因配置错误被挂起 |
| 3 | K8s State | kubernetes (fact-4b671b707958) | `Waiting: reason: "CreateContainerConfigError"` | 判定容器状态异常类型为配置错误 |
| 4 | Metric | prometheus (fact-0a91477bd3cf) | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` | 指标层面确认 Pod 处于配置错误等待状态 |
| 5 | K8s State | kubernetes (fact-b2803d386452) | `restart_count = 0` | 确认容器从未成功启动，处于持续重试配置阶段 |
| 6 | K8s State | kubernetes (fact-b1e4006855c9) | `Pod Status: Pending` | 用户可见现象：Pod 处于挂起状态 |

K8s Event（#1）明确指出了 `Secret aiops-case-04/workload-input` 中缺少 `unavailable-key` 这一具体配置缺陷；K8s State 的 Waiting Message（#2）和 Reason（#3）与此一致，Metric 数据（#4）进一步从监控侧佐证了该 Pod 处于 `CreateContainerConfigError` 状态。由于配置校验在容器启动前失败，容器重启次数为 0（#5），未产生后续日志或流量。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺少 key 'unavailable-key' → kubelet 解析挂载卷失败 → 容器创建被拒绝(CreateContainerConfigError) → Pod 持续 Pending 且无法产出流量/日志
```

### 根因结论

**已确认的根因**：Pod 定义中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 对象中不存在此 key，导致 kubelet 无法挂载配置并创建容器。

**证据支撑**：
- K8s Event 日志明确报错 `couldn't find key unavailable-key`（#1, #2）。
- 容器状态稳定为 `CreateContainerConfigError`（#3），Metric 确认该状态值（#4）。
- 配置层面的失败阻止了容器运行，因此无其他业务维度的证据需求。

---

## 📊 性能统计

```text
├─ 总耗时: 53.6s
├─ 问题定位: 15.4s
├─ 并发证据采集: 28.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 28.2s (Evidence 19.2s, RCA 8.9s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- 未调用 Runbook
