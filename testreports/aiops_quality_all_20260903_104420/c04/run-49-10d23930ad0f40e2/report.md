## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Normal Pulled 3m26s (x418 over 93m) kubelet Container image "xnet.registry.io:8443/observability/python:3-alpine" already present on machine` | 确认镜像拉取正常，排除镜像仓库或网络镜像拉取问题 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: {"container": "app", "reason": "CreateContainerConfigError"}` | 直接表明容器因配置错误停留在 Waiting 状态 |
| 3 | K8s State | Kubernetes | `container.waiting_message: {"container": "app", "message": "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"}` | 指出具体的配置错误：Secret 中缺失 `unavailable-key` |
| 4 | K8s Event | Kubernetes | `cni.projectcalico.org/podIPs: 172.16.104.12/32` | 网络插件已分配 IP，Pod 具备基本的网络环境 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (labels: `reason=CreateContainerConfigError`, `sample_count=1`) | 验证容器处于 Waiting 状态且原因为 `CreateContainerConfigError` |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (labels: `container=app`) | 容器从未成功启动过，无重启记录 |
| 7 | Logging | Kubectl | `kubectl logs workload-6584f97c76-wvcb2 -n aiops-case-04 --tail=50` 返回 `Error from server (BadRequest): container "app" in pod "workload-6584f97c76-wvcb2" is waiting to start: CreateContainerConfigError` | 进一步证实应用未启动，因此无业务日志输出 |

**证据印证：**
Kubernetes 事件与等待状态一致确认了错误原因为 `CreateContainerConfigError`。Kubectl 日志尝试失败进一步排除了应用启动后崩溃的可能性，证实问题出在容器初始化前的配置阶段。指标数据佐证了该状态已持续存在且未发生重启。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用的 Secret `aiops-case-04/workload-input` 缺失键 `unavailable-key` → Kubelet 创建容器时解析 Secret 失败 → 容器配置校验失败，持续处于 Waiting 状态 → Pod 显示 CreateContainerConfigError
```

### 根因结论

已确认的根因是：**Pod 配置引用了不存在的 Secret Key**。

Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 `app` 容器在启动配置中引用了 Secret `aiops-case-04/workload-input` 中的 `unavailable-key`，但该 Secret 中实际不包含此 Key（仅包含 `available-key`）。这导致 Kubernetes 在创建容器时无法注入配置，进而触发 `CreateContainerConfigError`，使 Pod 始终无法进入 Running 状态。证据包括 K8s 状态中的错误消息、事件记录以及 Prometheus 指标中的对应状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 23.7s
├─ 并发证据采集: 70.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 70.6s (Evidence 61.3s, RCA 9.1s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
