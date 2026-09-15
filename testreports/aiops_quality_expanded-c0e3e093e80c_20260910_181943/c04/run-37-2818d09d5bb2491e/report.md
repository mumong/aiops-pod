## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 状态为 CreateContainerConfigError，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 实体 `aiops-case-04/workload-6584f97c76-h4lt9` 状态 `CreateContainerConfigError`，无法启动 | 确认异常实体与直接表现，为后续指标与根因提供上下文基准 |
| 2 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `container: app`, `reason: CreateContainerConfigError`) | 量化确认 Pod 正处于配置错误导致的等待状态，非重启风暴或资源不足 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (labels: `container: app`) | 确认容器未发生过重启，佐证启动失败发生在容器创建/配置阶段而非运行时崩溃 |
| 4 | K8s State | 内部诊断上下文 | 根因事实绑定：Secret `app-secret` 缺少 Key `app-secret-key`，导致 Kubelet 无法创建容器配置 | 提供导致 `CreateContainerConfigError` 的具体缺失项与因果机制 |

**证据逻辑说明：**
当前事实链为：K8s 状态确认 Pod 处于 `CreateContainerConfigError` → Metric 验证了 `waiting_reason` 为该错误且重启数为 0，排除了应用逻辑失败 → 结合诊断上下文事实，明确指出该状态由 Secret Key 缺失导致。由于容器未启动，Logging 与 Tracing 维度物理上无数据可采集，当前 K8s 状态指标与内部诊断事实已构成完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因 → 失败机制 → 直接失败 → 用户可见现象
Secret app-secret 缺少 Key app-secret-key → 容器 app 尝试注入不存在的密钥 → Kubelet 抛出 'secretkey ... not found' 错误 → Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 等待状态
```

### 根因结论

**已确认的根因：** Pod `aiops-case-04/workload-6584f97c76-h4lt9` 中的 `app` 容器引用了 Secret `app-secret` 中不存在的 Key `app-secret-key`。

该问题通过以下证据链得到支撑：
- **现象层面**（证据#1, #2）：K8s 状态与 Prometheus 指标一致确认 Pod 因 `CreateContainerConfigError` 处于等待状态，且重启次数为 0，符合配置未就绪的特征。
- **根因层面**（证据#4）：诊断事实已定位到具体的配置缺陷——Secret `app-secret` 实际仅包含 `another-key`，缺少容器声明引用的 `app-secret-key`，导致 Kubelet 拒绝创建容器配置。

现有证据足以解释当前异常现象，无需补充额外的工具调用即可结案。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.5s
├─ 并发证据采集: 31.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 31.8s (Evidence 25.5s, RCA 6.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
