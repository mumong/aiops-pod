## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 Pending 阶段，容器 app 状态为 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod/condition | `ContainersReady: False (reason: ContainersNotReady)`<br/>`Ready: False (reason: ContainersNotReady)` | 确证 Pod 因容器不可用而处于不可读状态 |
| 2 | K8s Event | kubelet | `Error: Failed to pull image "registry.invalid/aiops/workload:missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供决定性证据，指明拉取失败的根本原因为 DNS 解析失败 |
| 3 | K8s Config | container.resource_limit | `memory: 32Mi, cpu: 50m` | 排除因资源限制（OOM/CPUThrottling）导致容器启动失败的干扰项 |
| 4 | K8s State | pod/phase | `Pending` | 反映 Pod 卡在调度或拉取阶段，尚未进入运行期 |
| 5 | Metric | kube_pod_container_status_waiting_reason | `reason: ErrImagePull` (value: 1) | 与 Kubernetes 事件中的拉取错误状态在指标层面形成交叉印证 |

**证据说明：**
核心诊断链条完全由 Kubernetes 维度的证据闭环支撑：
1. 事件日志明确指出在解析 `registry.invalid` 时遇到了 `no such host` 的 DNS 错误（事实 #2）。
2. 该错误直接导致了镜像拉取失败（`ImagePullBackOff`），进而使 Pod 停留在 `Pending` 阶段（事实 #1、#4）。
3. Prometheus 指标中的 `ErrImagePull` 等待原因与事件日志相互印证（事实 #5），确认了错误状态的持续性。
4. 由于容器始终未启动，日志和追踪维度被客观排除，资源限制配置也排除了其他常见的启动失败因素。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 中配置的镜像仓库地址 registry.invalid 为无效域名 → CoreDNS (127.0.0.53) 解析失败 (no such host) → kubelet 拉取镜像中断并进入重试退避 (ImagePullBackOff) → Pod 停留在 Pending 状态
```

### 根因结论

已确认的根因为：**镜像配置错误**。

Pod `workload-65b7f54794-nqrzv` 的容器配置中使用了无效的镜像域名 `registry.invalid`。当 `kubelet` 尝试拉取该镜像时，DNS 解析服务（CoreDNS）无法找到该主机名（`no such host`），导致底层 HTTP 请求失败。由于域名无效且不存在，重试将永远失败，从而导致容器状态一直维持在 `ImagePullBackOff`，Pod 始终处于 `Pending` 状态。该结论由明确的系统日志错误（事实 #2）与镜像拉取状态事实完全支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 40.7s (Evidence 33.5s, RCA 7.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
