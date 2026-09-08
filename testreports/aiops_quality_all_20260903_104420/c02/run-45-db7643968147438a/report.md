## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态等待原因为 `ImagePullBackOff` (fact-6dff1950da52, fact-adfe1be2abab) | 明确容器当前异常状态 |
| 2 | K8s Event | Kubernetes | kubelet 报错：`Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-3cbe433df7f5, fact-67b7759a8b75) | 直接指向镜像拉取失败的根因 |
| 3 | K8s State | Kubernetes | Pod 状态为 `Pending`，且容器重启次数为 `0` (fact-3e824a7cc91d, fact-1b2440ab515d) | 确认容器始终未能进入运行状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 中 `app` 容器对应 `ImagePullBackOff` 指标值为 `1` (fact-fe2ba8381adb) | 从监控维度独立印证容器等待状态 |

**证据说明：**
1. K8s Event 提供了导致等待状态的具体错误原因（镜像地址域名无效）。
2. K8s State 与 Metric 相互印证了该 Pod 的 `ImagePullBackOff` 状态，且排除了因启动后崩溃重启导致的问题（重启数为 0，且处于 Pending 阶段）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中使用的镜像仓库域名 registry.invalid 无效 → 容器运行时无法解析或连接该域名拉取镜像 → Pod 持续处于 ImagePullBackOff 等待状态 → 应用服务不可用
```

### 根因结论

**已确认的根因：**
容器定义中配置的镜像地址 `registry.invalid/aiops/workload:missing` 使用了无效的域名（或不可达的注册表），导致 kubelet 无法拉取镜像。
*   **证据支持：**
    *   事实 `fact-3cbe433df7f5` 和 `fact-67b7759a8b75` 显示 kubelet 明确报告了拉取该镜像失败的 BackOff 事件。
    *   事实 `fact-adfe1be2abab` 和 `fact-fe2ba8381adb` 确认了容器一直处于 `ImagePullBackOff` 状态。
    *   事实 `fact-1b2440ab515d` 显示重启计数为 0，表明 Pod 未能成功创建任何运行中的容器，完全处于拉取失败的等待期。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.9s
├─ 并发证据采集: 65.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 65.7s (Evidence 57.7s, RCA 7.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
