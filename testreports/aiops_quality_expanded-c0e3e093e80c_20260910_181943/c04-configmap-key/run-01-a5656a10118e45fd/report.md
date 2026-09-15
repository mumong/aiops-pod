## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod workload 处于 Pending 状态，容器 app 报 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-a002d6de255f` | status: Pending | 描述 Pod 的实时阻塞状态 |
| 2 | K8s Event | `fact-3acde8d05c19` | `Warning Failed... Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接指出配置引用的缺失键及报错内容 |
| 3 | K8s Config | `fact-0c18ee903c19` | container `app` resource_limit.memory: 32Mi | 描述容器内存资源硬限制配置 |
| 4 | K8s Config | `fact-237938f009e2` | container `app` resource_request.memory: 8Mi | 描述容器内存资源调度保留量配置 |
| 5 | K8s Config | `fact-990626b69b0e` | container `app` resource_limit.cpu: 50m | 描述容器 CPU 资源硬限制配置 |
| 6 | K8s Config | `fact-54c0eb40576f` | container `app` resource_request.cpu: 5m | 描述容器 CPU 资源调度保留量配置 |

**证据说明：**
`K8s Event` 明确记录了 kubelet 因无法在 ConfigMap 中找到键 'unavailable-key' 而导致的 `CreateContainerConfigError`。此配置错误直接导致 `K8s State` 显示容器处于 `Pending` 状态，且未触发过任何重启（重启数为 0）。`K8s Config` 中定义的内存与 CPU 限制/请求量虽存在，但与启动失败事件无因果关系。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置引用了 ConfigMap key 'unavailable-key' → ConfigMap aiops-case-v11/workload-input 实际仅包含 key 'available-key' → kubelet 校验失败并报错 → 容器创建失败导致 CreateContainerConfigError 和 Pending 状态
```

### 根因结论

已确认的根因是：Pod 规范中引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的键 `unavailable-key`。
该配置缺失触发了 kubelet 的校验机制（证据 2），导致容器无法进入运行状态，从而呈现出 `CreateContainerConfigError` 和 `Pending` 的症状（证据 1）。现有的 Kubernetes 事件事实足以支撑此根因结论，无需 Metrics、Logging 或 Tracing 进一步佐证。

---

## 📊 性能统计

```text
├─ 总耗时: 59.3s
├─ 问题定位: 15.9s
├─ 并发证据采集: 34.4s
│  └─ g1 aiops-case-v11/workload: 34.4s (Evidence 28.2s, RCA 6.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
