## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器 app 因 CreateContainerConfigError 卡在 Waiting 阶段，从未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet` | Container `app` waiting reason: `CreateContainerConfigError` (fact-e43e5a7e81e7) | 直接确认容器因配置解析失败未启动，非业务逻辑崩溃。 |
| 2 | K8s State | `kubelet` | Container `app` waiting message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-33a93d555683) | 精确指向缺失的 Secret key 及所属 Secret 名称，锁定根因对象。 |
| 3 | K8s Event | `kubelet` | Normal Pulled: `Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine` (fact-b75a29d8ee5c) | 排除镜像拉取问题，确认为配置阶段失败。 |
| 4 | K8s State | `kubelet` | Pod phase/status: `Pending` (fact-7dcc90a23c35, fact-91f50f6f747f) | 确认 Pod 卡在调度后的配置挂载阶段。 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` value: `1` (fact-e3c190d4bb39) | 验证集群层面该容器处于配置错误的等待状态。 |

**证据交叉验证：**
Kubernetes 状态中的等待消息（事实 #2）与等待原因（事实 #1）高度一致，明确了错误发生于容器启动前的配置检查阶段；Metric 数据（事实 #5）在集群层面复现了该配置错误的持续状态。事件日志（事实 #3）排除了运行时故障和镜像问题。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'aiops-case-04/workload-input' 缺失 key 'unavailable-key' → kubelet 解析容器环境变量/密钥配置失败 → 触发 CreateContainerConfigError → Pod 处于 Pending 状态，容器从未启动
```

### 根因结论

已确认的根因为 **Pod 配置中引用的 Secret 缺失必要环境变量 Key**。
具体而言，容器 `app` 试图从 Secret `aiops-case-04/workload-input` 中读取名为 `unavailable-key` 的配置项，但该项目不存在。这导致 kubelet 在启动容器前校验配置失败，直接抛出 `CreateContainerConfigError`（证据 #1, #2），进而使 Pod 保持在 `Pending` 状态且重启次数为 0（证据 #4, #5）。现有证据已充分覆盖故障现象与直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 16.3s
├─ 并发证据采集: 33.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 33.6s (Evidence 26.2s, RCA 7.3s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
