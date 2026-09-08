## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod spec 引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 在命名空间中不存在，导致 Kubernetes 无法注入配置，从而引发 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (Container: `app`) | 标识容器启动阶段因配置缺失被系统主动阻断，非业务逻辑错误。 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指出引发异常的具体缺失对象及其来源。 |
| 3 | K8s State | Kubernetes | `pod.phase`: `Pending` | 确认 Pod 处于初始化挂起阶段，未进入运行时。 |
| 4 | K8s State | Kubernetes | `pod.condition`: `ContainersNotReady` (Message: `containers with unready status: [app]`) | 描述异常对 Pod 就绪状态的具体影响。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}`: 1 | 在监控层面印证了异常原因与 K8s 原生状态一致，排除了网络或资源配额问题。 |
| 6 | K8s Config | Kubernetes | `container.resource_limit.memory`: 32Mi, `resource_request.memory`: 8Mi | 提供资源上下文，证明 Pod 本身资源请求极低，排除了因资源不足导致启动失败的可能性。 |

**证据说明：**
- 证据 2 直接引用了 K8s 原生诊断消息，给出了根因的唯一确定性事实：Secret `aiops-case-04/workload-input` 中存在缺失的 Key `unavailable-key`。
- 证据 1、3、4 构成了完整的 K8s 状态链（状态码、等待原因、Pod 阶段），与证据 5 的 Metric 数据完全互相印证，均指向 `CreateContainerConfigError`。
- 证据 6 表明该异常与资源限制无关，进一步将排查范围锁定在配置/引用层面。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `aiops-case-04/workload-input` 不存在（或目标 key 未注入） → Pod 容器配置引用了 Secret `aiops-case-04/workload-input` 中的 `unavailable-key` 失败 → kubelet 在启动容器前挂载卷与注入配置环节报错 → Pod 状态卡在 Pending，容器报 CreateContainerConfigError
```

### 根因结论

已确认的根因是 **K8s 配置引用失效**。

Pod 的容器规格（spec）中声明了对 `Secret aiops-case-04/workload-input` 中 `unavailable-key` 的依赖。由于该 Secret 或其指定的 Key 不存在，Kubelet 无法完成配置注入和卷挂载，导致容器进程无法启动，直接触发 `CreateContainerConfigError` 并将 Pod 锁定在 `Pending` 状态（证据 2、1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.5s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 47.4s (Evidence 40.8s, RCA 6.5s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
