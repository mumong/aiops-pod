## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_message` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 直接说明镜像拉取因退避机制失败，且明确指出镜像路径 |
| 2 | K8s State | `container.waiting_reason` | `ImagePullBackOff` | 确认当前 Pod 的核心异常状态为镜像拉取失败后的退避期 |
| 3 | K8s State | `pod.condition` | `ContainersReady=False`, `Ready=False`, reason: `ContainersNotReady` | 确认容器尚未就绪，且未因健康检查失败重启 (restart_count=0) |
| 4 | K8s State | `pod.phase` | `Pending` | 确认 Pod 未进入 Running 状态，调度阶段已完成但启动受阻 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `1` (label: `reason=ImagePullBackOff`) | 独立观测确认该 Pod 处于 ImagePullBackOff 状态 |
| 6 | K8s Config | `container.resource_limit.memory/cpu` | `32Mi/50m` | 资源限制配置正常，非 OOM 或 CPU 限制导致的问题 |

**证据说明**：
1. K8s 状态与 Metric 数据高度一致，均通过独立维度确认了 `ImagePullBackOff` 状态及未就绪事实。
2. 关键证据指向 `registry.invalid` 这一具体域名。该域名符合 RFC 2606 保留特征（用于测试文档），在真实生产环境中必然无法解析。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置使用了保留域名 registry.invalid → 容器运行时 DNS 解析失败 → Kubernetes 持续报 ErrImagePull 并进入 BackOff 退避 → Pod 保持 Pending 状态且处于 ImagePullBackOff
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-02/workload-65b7f54794-nqrzv` 配置了包含无效保留域名 `registry.invalid` 的镜像地址 (`registry.invalid/aiops/workload:missing`)。
这一配置直接导致容器运行时无法解析镜像仓库地址，触发 DNS 解析失败。Kubernetes 在重试拉取失败后进入 `ImagePullBackOff` 状态，导致 Pod 无法启动，表现为 `Pending` 阶段且 `ContainersReady=False`。证据中 `restart_count=0` 进一步排除了运行时崩溃重启的可能，确认为启动初期的拉取阻断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.7s
├─ 并发证据采集: 34.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 34.5s (Evidence 27.0s, RCA 7.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
