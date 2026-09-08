## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app waiting_reason: CreateContainerConfigError | 确认容器因配置错误无法启动的核心状态 |
| 2 | K8s Event | kubernetes | Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 明确 kubelet 挂载失败的具体原因是缺少 Secret 键值 |
| 3 | K8s Config | kubernetes | container.app resource_limit: memory 32Mi, cpu 50m | 排除资源超配导致 OOM 杀进程的可能 |

证据 1 与证据 2 互相印证，指出 Pod 处于等待状态的根本原因是 Secret 中的键值不匹配，导致 kubelet 无法完成配置挂载。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用不存在 key 'unavailable-key' → kubelet 挂载 Secret 失败 → 容器启动报错 CreateContainerConfigError → Pod 处于 Pending 状态
```

### 根因结论
已确认根因为 Pod Spec 错误引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`。
该错误导致 kubelet 无法挂载配置并启动容器，从而产生 `CreateContainerConfigError` 状态（证据 #1, #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.5s
├─ 并发证据采集: 47.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 47.2s (Evidence 38.6s, RCA 8.5s)
└─ 汇总总结: 5.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
