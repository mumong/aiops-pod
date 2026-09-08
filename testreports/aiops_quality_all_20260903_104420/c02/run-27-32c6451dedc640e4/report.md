## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... Error: ImagePullBackOff` (fact-0e5b1ba23ea0) | 确认容器等待状态为镜像拉取失败 |
| 2 | K8s Event | Kubernetes | `Warning Failed ... failed to do request: Head "https://registry.invalid/v2/...": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-f7d2b5761a29) | 确认直接原因为 DNS 解析失败，镜像仓库域名无效 |
| 3 | K8s Config | Kubernetes | container.waiting_message: `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-3d1b8e20d635) | 确认具体拉取失败的镜像及 Back-off 状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{...reason="ImagePullBackOff"} = 1` (fact-3f67c0528b19) | 通过指标确认当前 Pod 处于 ImagePullBackOff 状态 |

证据 1、2、3 均来源于 K8s 事件和状态，且相互印证：Kubelet 尝试拉取 `registry.invalid/aiops/workload:missing` 时，因 `registry.invalid` 无法解析（no such host）而失败，随后进入 Back-off 状态。指标事实 4 与 K8s 状态事实一致，确认了该现象在监控时间点的持续性。由于容器未启动，日志和链路追踪数据不可用（工具执行失败且容器状态不支持）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 镜像配置了无效域名 registry.invalid → DNS 解析失败 (no such host) → 镜像拉取失败 → Pod 处于 ImagePullBackOff 状态不可用
```

### 根因结论

已确认的根因是 Pod `aiops-case-02/workload-65b7f54794-rnlv4` 的容器配置了无效的镜像仓库域名 `registry.invalid`。
- **事实支撑**：K8s Event 明确指出 `failed to do request... lookup registry.invalid... no such host` (证据 #2)，且 `kubelet` 报告 `Error: ImagePullBackOff` (证据 #1)。
- **现象解释**：由于无法解析镜像仓库地址，容器无法下载镜像，导致 Pod 处于 `ImagePullBackOff` 状态（证据 #3、#4），用户可见服务不可用。
- **缺失环节**：无。根因直接由 K8s 事件中的 DNS 解析失败记录证实，无需进一步日志或指标推断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.1s
├─ 并发证据采集: 58.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 58.6s (Evidence 49.4s, RCA 9.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
