## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod配置使用了无效的镜像仓库域名'registry.invalid'，集群DNS无法解析该域名，导致镜像拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `reason: ImagePullBackOff` | 确证容器拉取失败的直接原因 (fact-3910084f0be4) |
| 2 | K8s State | kubernetes | `message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\""` | 提供导致失败的精确镜像源标识 (fact-400c8d3ae405) |
| 3 | K8s State | kubernetes | `phase: Pending` | 确认 Pod 停留在调度等待阶段，未进入运行态 (fact-2c285e3178be) |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `reason=ImagePullBackOff`) | 独立确认当前存在一个等待中的异常容器 (fact-d80f7238b11e) |

Kubernetes 状态与 Metric 均独立指向了同一个 `ImagePullBackOff` 状态，相互印证了镜像拉取故障的实时状态。日志与追踪维度因容器未启动显示为空，但不影响上述状态的确诊。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置使用了无效的镜像仓库域名'registry.invalid' → 集群DNS解析失败/网络不通 → 镜像拉取持续失败(ImagePullBackOff) → Pod停留在Pending状态且应用不可用
```

### 根因结论

**已确认的根因**：Pod 配置中使用了不可达或无效的镜像仓库域名 `registry.invalid`。

该域名无法解析，导致 kubelet 无法拉取镜像 `registry.invalid/aiops/workload:missing`。K8s 状态显示等待原因为 `ImagePullBackOff` (证据 1)，详细报错信息明确指出无法访问该域名 (证据 2)，Prometheus 指标确认该异常正在持续发生 (证据 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 40.0s (Evidence 35.5s, RCA 4.4s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
