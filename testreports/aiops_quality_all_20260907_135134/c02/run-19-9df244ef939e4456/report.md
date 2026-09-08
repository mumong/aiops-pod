## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | 镜像仓库域名 registry.invalid DNS 解析失败导致容器运行时无法拉取镜像 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason: {"container": "app", "reason": "ImagePullBackOff"}` (fact-96a98b4263bc) | 确认容器当前处于因镜像拉取失败导致的等待状态，是现象的根因定位点。 |
| 2 | K8s Event | kubernetes | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-accc6184a557) | 直接展示容器运行时尝试解析 `registry.invalid` 时遭遇的 DNS 解析失败错误。 |
| 3 | K8s Event | kubernetes | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-b9d9cd3f8bb7) | 确认 kubelet 已进入指数退避（Back-off）阶段，说明拉取失败已在持续发生。 |
| 4 | K8s State | kubernetes | `pod.phase: Pending` (fact-7556e7101d39) | 确认 Pod 未能进入 Running 状态，因容器无法就绪，符合拉取失败的阻塞逻辑。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason {reason="ImagePullBackOff"} = 1` (fact-7516f6177e85) | 从监控维度独立证实该容器目前处于 ImagePullBackOff 等待状态。 |

**证据分析：**
Kubernetes 事件 (fact-2) 提供了最完整的错误上下文，明确指出 `lookup registry.invalid ... no such host`，将故障原因锁定在 DNS 层面。这一事实解释了为什么容器状态 (fact-1) 呈现为 `ImagePullBackOff`，并且与 Metric 监控中的状态 (fact-5) 完全一致。由于容器未启动，Logging 和 Tracing 数据不可用，但这并不影响基于网络侧错误的诊断。

## 🎯 根因分析 · g1

```text
DNS 解析失败 (lookup registry.invalid: no such host) → 镜像拉取被拒绝 (ErrImagePull) → 容器启动失败并退避重试 (ImagePullBackOff) → Pod 持续处于 Pending 状态
```

**根因结论：**
已确认根因为**镜像仓库域名 `registry.invalid` 的 DNS 解析失败**（证据：fact-accc6184a557）。
Pod 无法拉取指定的镜像，导致容器无法启动，进而使 Pod 阻塞在 `Pending` 状态并伴随 `ImagePullBackOff` 警告。当前证据足以确认故障机理，缺失的事实仅为节点具体的 DNS 配置内容（`/etc/resolv.conf`）以及该域名是否为故意配置。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.8s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 41.5s (Evidence 33.0s, RCA 8.3s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
