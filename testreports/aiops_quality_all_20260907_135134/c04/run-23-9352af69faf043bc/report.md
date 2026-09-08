## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 容器配置引用了不存在的 Secret Key (`unavailable-key` in `aiops-case-04/workload-input`)，导致 kubelet 无法完成容器配置而陷入 `CreateContainerConfigError`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubelet | `container.waiting_reason`: CreateContainerConfigError (Container: app) | 直接指向容器配置阶段失败，未进入运行时 |
| 2 | K8s Event | Kubelet | `message`: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供精确失败原因：Secret Key 缺失 |
| 3 | K8s State | Pod Spec | `phase`: Pending, `container.restart_count`: 0 | 确认 Pod 停滞在初始化前阶段，无重试行为 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=`CreateContainerConfigError`, value=1, sample_count=1) | 从指标维度独立确认当前等待原因 |

**证据印证说明**：K8s 事件明确指出了 `Secret aiops-case-04/workload-input` 中缺失 `unavailable-key`，该原因直接导致了 `CreateContainerConfigError`。指标数据独立观测到了相同的等待原因状态。由于容器未能配置成功，Logging 与 Tracing 维度物理上无数据，不引入其他维度的证据冲突或补充。

## 🎯 根因分析 · g1

### 因果链

```text
Secret Key 配置错误 (`unavailable-key` 不存在) → 容器配置阶段失败 (CreateContainerConfigError) → 直接失败 (Pending / Wait) → 用户可见现象 (Pod 状态未就绪)
```

### 根因结论

已确认的根因为：**Pod 配置错误引用了不存在的 Secret Key**。

Pod `workload-6584f97c76-7ds5p` 的容器 `app` 试图从 Secret `aiops-case-04/workload-input` 中加载键名为 `unavailable-key` 的密钥，但该密钥在 Secret 对象中并不存在。该错误导致 kubelet 在“创建容器配置”阶段报错，致使容器无法启动并陷入 `CreateContainerConfigError` 等待状态。

* 支撑证据：K8s Event (`fact-ce8452023b9d`) 明确指出 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`；K8s State (`fact-242df771d7c6`) 确认了 `CreateContainerConfigError` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 56.7s
├─ 问题定位: 11.7s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 36.8s (Evidence 31.6s, RCA 5.0s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
