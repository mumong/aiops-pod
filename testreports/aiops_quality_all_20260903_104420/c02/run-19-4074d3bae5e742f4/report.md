## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod配置了无效的镜像仓库域名 registry.invalid，导致 Kubernetes kubelet 在拉取镜像时发生 DNS 解析失败（no such host），从而引发 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-386a323661a3) | `Failed to pull image "registry.invalid/aiops/workload:missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 记录 DNS 解析失败的原始错误原文，直接指向镜像域名无效 |
| 2 | K8s State | kubernetes (fact-7042282bd167) | `container.waiting_reason: ImagePullBackOff` | 确认容器的具体等待状态 |
| 3 | Metric | prometheus (fact-052440bae269) | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 独立指标验证容器处于拉取失败退避状态 |
| 4 | K8s State | kubernetes (fact-4d39d1c8670c) | `pod.phase: Pending` | 确认 Pod 始终处于挂起状态，未进入运行阶段 |

**证据说明**
Kubernetes Event 提供的 DNS 解析失败（`no such host`）与 `kubelet` 拉取镜像错误原文完全一致，确认为根因。Metric 数据从监控层独立印证了 `ImagePullBackOff` 状态，与 K8s 资源状态事实相互吻合，证实了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置无效域名 registry.invalid → DNS 解析失败 (no such host) → kubelet 拉取镜像失败 (ImagePullBackOff) → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为：Pod 配置了无效的镜像仓库域名 `registry.invalid`。
*   **证据支撑**：
    *   Event 事实 `fact-386a323661a3` 记录了明确的 DNS 解析失败错误原文（`lookup registry.invalid on 127.0.0.53:53: no such host`）。
    *   State 事实 `fact-7042282bd167` 记录了容器状态为 `ImagePullBackOff`。
    *   Metric 事实 `fact-052440bae269` 在监控层验证了同样的等待原因。
*   **结论**：无效域名导致 kubelet 无法解析和下载镜像，引发拉取失败及持续重试退避。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.6s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 55.2s (Evidence 48.2s, RCA 6.8s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
