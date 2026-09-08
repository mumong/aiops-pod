## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态且未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-9cc12dc23627) | 提供直接诊断依据，指出挂载失败的具体原因 |
| 2 | K8s State | kubernetes | 容器重启次数 `restart_count: 0` (fact-88a014d84ad3) | 佐证容器尚未启动，排除运行时崩溃 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 `1`，标签 `reason: CreateContainerConfigError` (fact-df436c34a08d) | 从监控维度确认当前的异常状态 |
| 4 | K8s Config | kubernetes | Pod 配置请求/限制（如 CPU `5m`，内存 `8Mi` 等）(fact-c2e86b5b7952 等) | 排除因资源不足导致调度或启动失败 |

**证据关联：**
`kubelet` 明确报告无法在 Secret 中找到指定 key（证据 #1），这导致容器无法启动。Prometheus 监控确认了 `CreateContainerConfigError` 状态（证据 #3），且重启计数为零（证据 #2），排除了应用启动后崩溃的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺少 key 'unavailable-key' → kubelet 挂载 Secret 失败 → 容器启动受阻，进入 CreateContainerConfigError 状态 → Pod 持续处于 Pending/异常状态
```

### 根因结论

已确认根因：Pod 配置中引用了 `Secret aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 key 在该 Secret 中不存在。

这一配置错误导致 kubelet 无法成功挂载所需的 Secret 卷，直接阻止了容器的创建和启动（证据 #1、#3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 28.0s
├─ 并发证据采集: 52.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 52.7s (Evidence 41.7s, RCA 10.9s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
