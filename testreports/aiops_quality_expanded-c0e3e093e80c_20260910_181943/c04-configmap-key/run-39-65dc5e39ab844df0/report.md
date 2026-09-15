## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | ConfigMap 'aiops-case-v11/workload-input' 中缺少 Pod 配置引用的键 'unavailable-key'，导致 kubelet 无法创建容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-ed8cf80d2292` | Container `app` 处于 `Waiting` 状态，原因 `CreateContainerConfigError` | 直接展示当前异常终端状态 |
| 2 | K8s State | `fact-f666f065152d` | Container `app` 报错信息：`couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接指出具体的缺失资源路径 |
| 3 | K8s Event | `fact-6a5c3e25111c` | `Warning Failed` 事件：kubelet 连续 12 次尝试创建容器失败，提示找不到 key `unavailable-key` | 确认 kubelet 侧重复失败机制与具体错误原因 |
| 4 | K8s State | `fact-2306115db504` | Pod 状态为 `Pending`，Pod Phase 为 `Pending` | 反映容器未成功创建，Pod 停留在未调度完成阶段 |
| 5 | Metric | `fact-3915c2dbea92` | `kube_pod_container_status_waiting_reason=1`，标签 `reason="CreateContainerConfigError"`，`container="app"` | 独立维度确认容器正在处于配置错误的等待状态 |

**证据说明：**
Kubernetes 状态显示容器因找不到 ConfigMap 中的 key 而报错 `CreateContainerConfigError` [1][2]，事件日志证实了 kubelet 连续多次因同样原因失败 [3]。Prometheus 指标进一步佐证了容器正处于该错误状态，且重启次数为 0，说明故障发生在容器启动初期的配置挂载阶段 [4][5]。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 缺失键 'unavailable-key' → Kubelet 挂载配置失败并持续重试 → 容器状态保持 Waiting (CreateContainerConfigError) → Pod 处于 Pending 状态且无法运行
```

### 根因结论

已确认根因为 ConfigMap `aiops-case-v11/workload-input` 中缺少 Pod 配置引用的键 `unavailable-key`。

该缺失导致 kubelet 无法完成容器创建阶段的环境变量或卷挂载配置，进而触发 `CreateContainerConfigError` 异常（证据 1, 2, 3）。容器未能成功启动且未发生过重启，因此 Pod 停留在 `Pending` 状态（证据 4, 5）。目前证据链完整，足以解释当前异常现象，无需进一步排查其他维度。

---

## 📊 性能统计

```text
├─ 总耗时: 55.5s
├─ 问题定位: 15.8s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-v11/workload: 30.6s (Evidence 24.0s, RCA 6.6s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
