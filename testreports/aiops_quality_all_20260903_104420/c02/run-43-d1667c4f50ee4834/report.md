## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4持续处于ImagePullBackOff状态，容器从未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: "ImagePullBackOff" (fact-59db4d8fb475) | 确认容器因镜像拉取失败而进入等待状态 |
| 2 | K8s State | kubernetes | `container.waiting_message`: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" (fact-0b59e85b30b6) | 揭示具体的镜像引用及拉取失败详情 |
| 3 | K8s Event | kubernetes | "Normal  BackOff  38s (x372 over 85m)  kubelet  Back-off pulling image \"registry.invalid/aiops/workload:missing\"" (fact-6328537d83bf) | 证实kubelet在85分钟内进行了372次拉取重试 |
| 4 | K8s State | kubernetes | `pod.status`: "Pending", `pod.phase`: "Pending" (fact-274c68772d91, fact-54eb45734ee6) | 确认Pod因未运行容器而停留在Pending阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = 1 (fact-62c2ff7684ad) | 监控指标直接映射到镜像拉取失败的Waiting状态 |

**证据分析说明：**
1. **现象印证**：Kubernetes状态、事件与Prometheus指标三方数据一致，共同指向 `ImagePullBackOff` 异常。
2. **根因指向**：事实 #2 与 #3 中的具体镜像路径 `registry.invalid/aiops/workload:missing` 揭示了失败的直接原因。`registry.invalid` 为RFC 2606保留域名，该域名无效导致kubelet无法解析和连接镜像服务。
3. **缺失维度**：由于容器从未启动（事实 #4），物理上无法产生应用层日志（Logging）或业务调用（Tracing），且工具采集失败记录证实了这一点（如 `query_pod_logs` 因权限被拒绝且Pod未启动而失败）。因此，判定根因仅依赖K8s与Metric维度即可闭环。

## 🎯 根因分析 · g1

### 因果链

```text
配置了保留无效域名 registry.invalid 的镜像引用 → kubelet尝试拉取镜像因域名无法解析而失败 → kubelet进入BackOff重试机制(372次/85分钟) → 容器始终处于Waiting(ImagePullBackOff)状态，Pod处于Pending
```

### 根因结论

**已确认的根因**：
Pod (`aiops-case-02/workload-65b7f54794-rnlv4`) 配置了无效的镜像仓库域名 `registry.invalid`（事实 #2）。该域名属于RFC 2606保留域名，环境内未配置DNS重定向或Host映射（未知项），导致 `kubelet` 在拉取镜像 `registry.invalid/aiops/workload:missing` 时持续失败。

该机制触发了Kubernetes的指数退避重试策略，在85分钟内累积了372次拉取失败（事实 #3），使容器状态锁定在 `ImagePullBackOff`，Pod状态锁定在 `Pending`，表现为容器无法启动（事实 #1、#4）。Prometheus指标与K8s事件完全印证了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.2s
├─ 并发证据采集: 63.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 63.1s (Evidence 52.3s, RCA 10.6s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
