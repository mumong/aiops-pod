## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 Pending 状态，Container 'app' 持续报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning Failed: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接定位挂载失败原因 |
| 2 | K8s State | kubernetes | container `app` 处于 `waiting` 状态，原因为 `CreateContainerConfigError` | 确认容器启动受阻的确切阶段 |
| 3 | K8s Config | kubernetes | 资源请求：CPU 5m, Memory 8Mi；资源限制：CPU 50m, Memory 32Mi | 排除资源规格不匹配导致创建失败 |
| 4 | K8s State | kubernetes | Pod 处于 `Pending` 阶段，`Ready` 条件为 False (`ContainersNotReady`) | 确认 Pod 整体不可用且未调度启动 |

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 Secret key 'unavailable-key' → kubelet 挂载 Secret 失败触发 CreateContainerConfigError → Container 'app' 状态保持 Waiting → Pod 呈现 Pending 状态
```

### 根因结论

已确认的根因是 **Secret 配置错误**。Pod 的 `app` 容器在启动时，kubelet 尝试从 Secret `aiops-case-04/workload-input` 中读取名为 `unavailable-key` 的字段（证据 #1），但该 key 实际上不存在。这一配置错误导致容器无法完成配置加载，从而进入 `CreateContainerConfigError` 等待状态（证据 #2），最终致使 Pod 持续处于 Pending 状态（证据 #4），无法对外提供服务。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.0s
├─ 并发证据采集: 37.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 37.7s (Evidence 29.9s, RCA 7.7s)
└─ 汇总总结: 6.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
