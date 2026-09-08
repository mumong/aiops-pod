## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason` = "ImagePullBackOff" (`fact-8546cd63b2c7`) | 确认容器未启动的当前状态 |
| 2 | K8s Event | Kubernetes | `Normal BackOff 92s (x284 over 66m) Back-off pulling image "registry.invalid/aiops/workload:missing"` (`fact-7793057bf9b1`) | 直接记录拉取镜像失败的详细原因 |
| 3 | K8s State | Kubernetes | `pod.phase` = "Pending", `ready` = "False" (`fact-27f3356e1c49`, `fact-219da8fecdb0`) | 确认 Pod 调度完成但容器未就绪 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = "1" (`fact-664a9d90c9c8`) | 独立于 K8s 状态机的指标佐证，确认等待原因为拉取失败 |
| 5 | Logging | Kubernetes/ES | `kubectl logs ... Error: container "app" in pod ... is waiting to start: trying and failing to pull image` (`fact-20fa91b2c109`) | 命令行工具反馈镜像拉取失败，确认未启动前无业务日志 |

证据表明，Pod 处于 Pending 且未 Ready 状态，所有指标和事件均一致指向镜像拉取（Pulling）阶段失败。K8s Event 与 Metrics 互为印证，日志失败信息进一步排除了启动后崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置无效镜像地址 registry.invalid → Kubelet 解析域名失败 → 镜像拉取反复失败并 BackOff → Pod 持续处于 ImagePullBackOff (Pending)
```

### 根因结论

已确认根因为 **Pod 配置了无效镜像仓库地址**，导致镜像拉取永久失败。

**证据支撑：**
- **现象确认**：K8s State 显示 `container.waiting_reason="ImagePullBackOff"` 且 `pod.phase="Pending"`，容器未进入运行阶段（证据 #1, #3）。
- **原因指向**：K8s Event 明确记录了具体失败的操作与镜像名称：`Back-off pulling image "registry.invalid/aiops/workload:missing"`（证据 #2）。该镜像地址指向的 TLD `.invalid` 为保留域名，不可解析，这是导致拉取失败的直接物理原因。
- **外部印证**：Prometheus 指标 `kube_pod_container_status_waiting_reason` 显示 `reason="ImagePullBackOff"` 值为 1，确认了该状态的真实性（证据 #4）；`kubectl logs` 尝试获取日志时明确报错 `container "app" in pod ... is waiting to start: trying and failing to pull image`，证实容器从未被成功启动（证据 #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 13.3s
├─ 并发证据采集: 76.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 76.3s (Evidence 67.8s, RCA 8.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
