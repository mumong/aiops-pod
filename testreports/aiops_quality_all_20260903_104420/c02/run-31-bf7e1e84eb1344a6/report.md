## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，Pod Phase 为 Pending，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-529124103e0c` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (持续 65m) | 直接证明镜像拉取失败及系统进入指数退避状态 |
| 2 | K8s Event | `fact-5ded02c2df99` | `Annotations: cni.projectcalico.org/containerID: ...` | 证明 Pod 基础调度成功且 CNI 网络已正确配置 |
| 3 | K8s Config | `fact-4b95a80afd16` | `container.waiting_reason: "ImagePullBackOff"` | 确认当前核心异常状态 |
| 4 | Metric | `fact-d4dd2d5602d6` | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 时序数据佐证 Kubernetes 层面拉取镜像失败的确定性 |

当前日志与追踪维度因采集权限限制及容器未启动状态，物理上无有效数据支撑，但 K8s 原生事件与时序指标已充分暴露“镜像仓库域名无效”这一核心事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用无效域名 registry.invalid 且未配置 imagePullSecrets → 域名 DNS 解析失败 (NXDOMAIN) 且网络不可达 → 镜像拉取连续失败触发 BackOff 退避机制 → Pod 持续处于 ImagePullBackOff 状态且容器未启动
```

### 根因结论

**已确认根因：镜像仓库配置错误（域名无效）**

证据充分表明故障根因为 Pod 配置中的镜像地址 `registry.invalid/aiops/workload:missing` 使用了无效的域名（`registry.invalid`），导致节点 kubelet 无法解析该域名并拉取容器镜像。

- **证据支撑**：
  - 异常组事实直接记录了容器等待原因为 `ImagePullBackOff`，且重复触发的 K8s 事件（#1, #2）明确报错 `Back-off pulling image "registry.invalid/aiops/workload:missing"`。
  - 度量指标（#4）确认容器状态处于 `ImagePullBackOff`，佐证了拉取操作的持续失败。
- **补充说明**：由于日志和追踪维度被标记为 `not_applicable` 或工具采集权限受限（`query_rejected`），本诊断未依赖应用层日志，完全基于 Kubernetes 原生调度事件与状态得出上述结论。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 16.2s
├─ 并发证据采集: 122.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 122.2s (Evidence 112.0s, RCA 10.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
