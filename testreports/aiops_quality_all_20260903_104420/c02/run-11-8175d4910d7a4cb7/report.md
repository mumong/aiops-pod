## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: ErrImagePull` (fact-05dd7164ef04); `Failed to pull image "registry.invalid/aiops/workload:missing": ... no such host` (fact-493bc20cc529) | 记录镜像拉取失败的具体错误机制，确认 DNS 解析失败 |
| 2 | K8s Event | Kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-51067dc4aa1b); `ImagePullBackOff` (fact-bfbe7c6e8bf4) | 确认因反复拉取失败导致的指数退避状态，形成直接现象 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ImagePullBackOff` (fact-1591e49a06ef); `pod.phase: Pending` (fact-14492709c37b) | 描述容器的当前生命周期阶段，确认 Pod 无法进入运行态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ImagePullBackOff, value=1) (fact-4e2d2cf754f4) | 从监控层面确认 Pod 容器当前正持续处于 ImagePullBackOff 状态 |

**证据交叉印证：**
Kubernetes Event 中的 `no such host` 错误明确指向了 `registry.invalid` 域名解析失败，进而导致 `ErrImagePull` 和 `ImagePullBackOff` 状态的发生，这与 Metrics 中展示的 `ImagePullBackOff` 状态（fact-4e2d2cf754f4）完全一致，确认了拉取失败及其后续退避机制是直接现象。

## 🎯 根因分析 · g1

### 因果链

```text
DNS解析失败(registry.invalid在节点127.0.0.53上NXDOMAIN) → kubelet连接中断(dial tcp no such host) → 镜像拉取失败及指数退避(ImagePullBackOff) → Pod持续处于Pending状态
```

### 根因结论

已确认的根因是 **Pod 配置了无效的镜像仓库域名 (`registry.invalid`)**。根据 K8s Event (fact-493bc20cc529, fact-cd5c3f6ca3f3) 的真实日志，Kubelet 尝试通过节点内置 DNS `127.0.0.53` 解析该域名时收到 `no such host` 响应，导致 HTTPS 请求无法建立，从而引发 `ErrImagePull` 并进入 `Back-off` 模式。该根因直接解释了为何容器处于 `ImagePullBackOff` (fact-1591e49a06ef) 且 Pod 保持 `Pending` (fact-14492709c37b) 的状态。由于容器根本无法启动，Logging 与 Tracing 维度因无运行进程而呈现 `not_applicable`，无法提供额外的业务侧约束或限定证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.0s
├─ 并发证据采集: 61.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 61.3s (Evidence 50.3s, RCA 10.8s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
