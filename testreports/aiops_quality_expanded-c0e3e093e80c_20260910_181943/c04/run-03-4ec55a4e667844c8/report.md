## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 Pending 状态，容器状态为 Waiting, Reason=CreateContainerConfigError，重启次数为0 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... 10m (x12 over 12m) kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确证直接失败机制：Secret 中缺失环境变量引用键 |
| 2 | K8s State | kubernetes | `status: Pending`, `restart_count: 0` (container: app) | 确认当前异常状态及无重启行为，与配置错误导致无法启动一致 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=CreateContainerConfigError) = 1 | 从监控数据角度独立印证容器处于配置错误等待状态 |

证据表明：K8s 事件明确指出了 Secret 键缺失是触发失败的具体原因，Metric 数据与该事件所指示的 `CreateContainerConfigError` 状态完全对应，且 Pod 处于 `Pending` 状态且重启次数为 0，进一步排除了运行时崩溃或启动失败的可能性，确认为启动前的配置解析失败。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 模板引用不存在 key → Secret 解析失败导致 CreateContainerConfigError → Pod 保持 Pending 状态 | 无重启 | 等待人工干预
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-04/workload-6584f97c76-h4lt9` 无法启动的直接原因是容器环境变量配置引用了不存在的 Secret Key `'unavailable-key'`。
- **证据 1 (K8s Event)** 直接捕获了 Kubelet 的报错信息：`couldn't find key unavailable-key in Secret aiops-case-04/workload-input`，明确了缺失的对象。
- **证据 2 (K8s State)** 展示了 Pod 持续处于 `Pending` 且重启次数为 `0`，符合因静态配置错误导致容器无法创建的特征。
- **证据 3 (Metric)** 中的 `CreateContainerConfigError` 指标与 K8s 事件完全吻合，提供了时间线上的独立验证。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 19.8s
├─ 并发证据采集: 552.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 552.7s (Evidence 544.6s, RCA 8.0s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
