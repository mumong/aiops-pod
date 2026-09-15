## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod 'workload' is stuck in 'Pending' state with container status 'CreateContainerConfigError', preventing startup. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-7575353e94ab) | 直接指出 Pod 启动时因 ConfigMap 缺少指定键而导致的失败原因 |
| 2 | K8s Config | Kubernetes | `resource_limit.cpu: 50m` (fact-2ef9d21d6c64), `resource_request.memory: 8Mi` (fact-516e130bcb1a), `resource_limit.memory: 32Mi` (fact-9f2894be30f3) | 排除因资源配额不足导致调度或启动失败的可能性 |
| 3 | K8s State | Kubernetes | `pod.status: Pending` (fact-a9febcc6ef8a), `container.restart_count: 0` (fact-83aca969fc2a) | 确认 Pod 处于初始化受阻状态，且未发生过重启 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `CreateContainerConfigError`) (fact-cf087e3ff4ae) | 独立验证了容器的等待原因为配置错误，与 K8s Event 现象一致 |
| 5 | K8s Event | Kubernetes | `network-status`, `podIPs`, `Annotations: cni.projectcalico.org/containerID: 6d98...` (fact-180e1fe5ba83 ~ fact-de4140520d07) | 网络插件已分配 IP 及容器 ID，确认底层网络层就绪，故障点仅在容器配置注入阶段 |

**证据分析：**
Kubernetes 事件日志提供了直接的错误文本（fact-1），明确指出 ConfigMap `aiops-case-v11/workload-input` 中缺少键 `unavailable-key`。Metric 数据（fact-4）独立证实了容器卡在 `CreateContainerConfigError` 状态。Pod 状态为 `Pending` 且重启次数为 0，结合已分配 IP 但未能启动的事实，排除了网络或资源限制问题，确认为配置注入阶段的静态失败。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 中缺少 'unavailable-key' → Pod 启动时环境变量/配置注入失败 (CreateContainerConfigError) → 容器无法初始化 → Pod 保持在 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-v11/workload` 的 Manifest 中错误引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的键 `unavailable-key`，导致 `kubelet` 无法完成容器环境变量的配置（fact-1）。

该配置错误直接引发了 `CreateContainerConfigError` 状态（fact-4），使得 Pod 无法进入 `Running` 状态，表现为持续的 `Pending` 状态（fact-3）。所有 K8s 状态、事件及 Metric 指标均一致指向此配置缺失问题。

---

## 📊 性能统计

```text
├─ 总耗时: 9.5m
├─ 问题定位: 13.2s
├─ 并发证据采集: 548.8s
│  └─ g1 aiops-case-v11/workload: 548.8s (Evidence 542.3s, RCA 6.4s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
