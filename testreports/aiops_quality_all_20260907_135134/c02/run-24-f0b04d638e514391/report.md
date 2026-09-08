## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置使用了无效的镜像仓库域名 `registry.invalid`，导致 kubelet 在尝试拉取镜像时 DNS 解析失败（`no such host`），从而引发 `ImagePullBackOff`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning  Failed ... Error: ImagePullBackOff` | 指示容器启动受阻的直接症状 |
| 2 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供具体的 DNS 解析失败错误，锁定根因为无效镜像域名 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason: ImagePullBackOff) | 从监控视角确认当前状态为 ImagePullBackOff |
| 4 | K8s Config | kubernetes | `container.resource_request.memory=8Mi`, `container.resource_limit.memory=32Mi` | 排除因资源不足导致的启动失败（资源配置处于合理范围） |
| 5 | K8s State | kubernetes | `pod.status: Pending`, `container.restart_count: 0` | 确认容器尚未成功拉起，且无重启尝试记录，符合刚配置错误镜像的特征 |

证据内容总结：
Kubernetes 事件与 Metric 均一致指向 `ImagePullBackOff` 状态。最关键的证据（事实 #2）明确指出 Docker/kubelet 在尝试连接 `registry.invalid` 时遭遇 `no such host` 错误，证实了镜像地址配置错误是根本原因。资源配置和重启次数等状态排除了其他潜在因素。

## 🎯 根因分析 · g1

### 因果链

```text
无效镜像域名 "registry.invalid" 配置 → DNS 解析失败 (no such host) → kubelet 镜像拉取错误 → ImagePullBackOff
```

### 根因结论

**已确认的根因**：Pod 配置了无效的镜像仓库域名 `registry.invalid`。

根据事实 #2，kubelet 尝试拉取 `registry.invalid/aiops/workload:missing` 时，底层网络请求在解析域名阶段失败（`lookup registry.invalid ... no such host`）。这直接导致容器处于等待状态，并触发 `ImagePullBackOff` 事件（事实 #1, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.8s
├─ 问题定位: 16.7s
├─ 并发证据采集: 29.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 29.4s (Evidence 24.3s, RCA 5.0s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
