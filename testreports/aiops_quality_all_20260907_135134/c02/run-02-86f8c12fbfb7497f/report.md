## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ErrImagePull | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 Pending 状态，容器 app 因 ImagePullBackOff 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证明镜像拉取失败是由于 DNS 解析错误导致 |
| 2 | K8s Event | kubelet | `Warning Failed ... Error: ErrImagePull` | 持续确认容器镜像拉取一直失败 |
| 3 | K8s Event | kubelet | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 证实 kubelet 进入退避重试状态 |
| 4 | K8s State | Pod.Status | `phase: Pending`, `status: Pending` | 确认 Pod 处于调度成功但容器无法运行的等待阶段 |
| 5 | K8s State | Container.Waiting | `reason: ImagePullBackOff`, `message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\""` | 确认容器因拉取镜像问题进入退避状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: `ImagePullBackOff`, value: `1`) | 从监控侧独立印证容器目前正等待镜像拉取 |

K8s Event 提供了具体的报错根因（DNS `no such host`），K8s State 证实了容器处于 `ImagePullBackOff` 的滞留状态，Metric 从系统侧提供了相同状态的交叉验证。Log 和 Tracing 因容器未启动而无数据，符合物理预期，不阻碍结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像配置使用了无效域名 'registry.invalid' (无 imagePullSecrets) 
→ kubelet 尝试拉取镜像时遭遇 DNS 解析失败 (no such host) 
→ 镜像拉取流程中止并进入退避状态 (ImagePullBackOff) 
→ Pod 状态长期保持 Pending，无法运行
```

### 根因结论

已确认根因为 **容器镜像仓库配置无效（DNS 解析失败）**。

证据（#1、#2、#3）明确显示，Kubelet 在尝试拉取 `registry.invalid/aiops/workload:missing` 镜像时，DNS 查询返回 `no such host` 错误。这一网络解析失败直接导致拉取中止，进而触发 K8s 的退避机制（#3、#5），使得 Pod 停留在 Pending 状态（#4、#6）。现有证据完整，无需进一步推测。

---

## 📊 性能统计

```text
├─ 总耗时: 58.2s
├─ 问题定位: 16.8s
├─ 并发证据采集: 32.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 32.4s (Evidence 25.6s, RCA 6.7s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
