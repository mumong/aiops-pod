## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod YAML 中配置的镜像仓库域名 'registry.invalid' 无效，导致 kubelet 在拉取镜像时发生 DNS 解析失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ErrImagePull` (fact-1abcee931023) | 记录拉取失败的具体事件 |
| 2 | K8s Event | kubelet | `Error: ImagePullBackOff` (fact-54d1d8918bc6) | 确认 kubelet 处于 BackOff 状态 |
| 3 | K8s Event | kubelet | `Error: Failed ... dial tcp: lookup registry.invalid ... no such host` (fact-b72a6f9acbb3) | 提供根本原因：DNS 解析失败，域名无效 |
| 4 | K8s State | kubelet | Container Waiting: `ImagePullBackOff`, Message: `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-af80b4be801b) | 容器等待状态的直接证据与镜像路径 |
| 5 | K8s State | kubelet | Container Waiting: `ImagePullBackOff` (fact-69b76b918dc4) | 确认 `app` 容器的失败原因 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason=`ImagePullBackOff`) (fact-f86d07e330fc) | 独立确认容器处于等待状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` (fact-57389b0e5550) | 确认应用未成功启动过，无重启历史 |

Kubernetes 事件直接指出了 DNS 解析失败和具体的无效镜像路径 `registry.invalid`。Prometheus 监控独立确认了容器处于 `ImagePullBackOff` 状态且未发生过重启，排除了应用启动后因 OOMKilled 等导致重启的情况，二者互相印证了镜像拉取故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置了无效域名 'registry.invalid' → kubelet 拉取镜像时发生 DNS 解析失败 (no such host) → 镜像拉取持续失败 (ErrImagePull / ImagePullBackOff) → 容器等待中，Pod 状态 Pending 且不可用
```

### 根因结论

已确认根因为 **Pod YAML 中配置的镜像仓库域名 `registry.invalid` 无效，导致 kubelet 在拉取镜像时发生 DNS 解析失败**。

证据充分：
1.  **Kubernetes Event** 明确指出 DNS 解析失败 (`lookup registry.invalid ... no such host`)，这是拉取失败的直接系统级错误 (fact-b72a6f9acbb3)。
2.  **Kubernetes State & Event** 显示容器因镜像拉取失败进入 `ImagePullBackOff` 状态 (fact-af80b4be801b, fact-69b76b918dc4)。
3.  **Prometheus Metric** 独立确认了容器处于 `ImagePullBackOff` 等待状态 (fact-f86d07e330fc)。

以上事实形成了完整的闭环：配置错误 -> 网络/DNS 解析失败 -> 镜像拉取终止 -> 容器状态停滞。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.4s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 40.0s (Evidence 35.0s, RCA 4.9s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
