## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod配置的镜像仓库registry.invalid不可达（DNS解析失败） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器状态等待原因: `ImagePullBackOff` (fact-58b65d8300c6) | 明确 Pod 异常终止/启动阶段状态 |
| 2 | K8s Event | Kubernetes | `Error: ErrImagePull` (fact-7520f3900de2) | 触发初始镜像拉取失败的直接证据 |
| 3 | K8s Config | Kubernetes | 期望拉取镜像: `registry.invalid/aiops/workload:missing` (fact-1ee9dc3c22d1) | 提供故障涉及的镜像及仓库地址，是验证可达性的关键目标 |
| 4 | K8s Event | Kubernetes | DNS解析失败详情: `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-1ee9dc3c22d1) | 证实因域名无法解析导致 Docker/Containerd 无法建立网络连接 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = 1 (fact-3bcd462ea791) | 从监控维度确认容器当前处于拉取失败的等待状态，与 K8s State 相互印证 |

**证据分析：**
Kubernetes Event 记录了完整的诊断链条：从触发 `ErrImagePull` 到进入 `ImagePullBackOff` 状态。关键事实 fact-1ee9dc3c22d1 直接提供了底层网络失败的原始报错（DNS 解析失败），直接锁定了镜像地址 `registry.invalid` 无效。Metrics 数据在 fact-3bcd462ea791 中确认了该等待状态仍持续存在。由于容器未启动，Logging 和 Tracing 为空，证据完全基于 K8s 原生状态和监控数据。

## 🎯 根因分析 · g1

```text
配置了不可用的镜像仓库 registry.invalid (事实3, 4) → DNS解析失败导致网络建立失败 (事实4) → kubelet 拉取镜像被拒绝并触发重试 (事实1, 2) → Pod 进入 ImagePullBackOff 等待状态 (事实5)
```

**根因结论：**
已确认根因为 **Pod 配置的镜像仓库不可达（DNS解析失败）**。
事实 1、2 和 3 证实了镜像拉取失败的直接对象，而事实 4 提供了决定性证据：系统尝试解析 `registry.invalid` 时返回 `no such host`。这导致 kubelet 无法连接该镜像仓库拉取镜像，最终容器维持在 `ImagePullBackOff` 状态（事实 1 和 5）。当前证据链完整且无冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 17.1s
├─ 并发证据采集: 87.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 87.2s (Evidence 83.1s, RCA 3.9s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
