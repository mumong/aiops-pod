## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p (aiops-case-04) stuck in CreateContainerConfigError, 0/1 Ready |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`="CreateContainerConfigError" (`fact-e462ca2b3e7e`) | 直接确认异常状态为配置注入阶段失败 |
| 2 | K8s State | Kubernetes | `container.waiting_message`="couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (`fact-e79b3b5da378`) | 提供根本原因的具体细节，指认缺失的资源标识符 |
| 3 | K8s State | Kubernetes | `pod.phase`="Pending", `container.restart_count`=0 (`fact-d9d1dace94de`, `fact-a32c9fbe54c7`) | 排除因资源不足或反复重启导致的故障，确认容器从未成功运行 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`="1" (reason=CreateContainerConfigError) (`fact-184938454532`) | 监控数据佐证 Kubernetes API 中的配置报错 |

上述证据链闭环：Kubernetes API 明确指出了具体的缺失配置项（事实 1、2），Metric 数据确认了该状态在监控时间窗口内持续存在（事实 4），同时重启次数为 0 的事实排除了运行时资源耗尽等干扰因素（事实 3）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 Secret key 'unavailable-key' → Kubelet 在创建容器时注入 secret volume 失败 → 容器创建过程报错 'couldn't find key unavailable-key' → Pod 停留在 CreateContainerConfigError 且处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 Secret 键**（证据编号 1、2）。Pod 规格中显式引用了 Secret `aiops-case-04/workload-input` 中的 `unavailable-key`，但该密钥在实际 Secret 中不存在。Kubelet 在尝试挂载该配置时因找不到密钥而中止容器创建，导致 Pod 无法进入 Running 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.8s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 39.5s (Evidence 32.0s, RCA 7.3s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
