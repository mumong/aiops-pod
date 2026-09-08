## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | 容器 `app` 处于 `ErrImagePull` 状态 | 直接定义当前异常阶段 |
| 2 | K8s State | `container.waiting_message` | `failed to resolve reference "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 定位具体失败机制为域名解析失败 |
| 3 | K8s Event | `event.message` | 8 条 `Warning Failed` 事件，包含 `ErrImagePull` 和 `ImagePullBackOff` 状态流转 | 确认异常持续发生 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `reason="ImagePullBackOff"` 值为 1，样本数 1 | 独立验证 K8s 状态 |
| 5 | K8s Config | `container.image` (上下文) | 目标镜像为 `registry.invalid/aiops/workload:missing` | 提供无效域名的配置来源 |
| 6 | K8s State | `pod.status` | Pod 阶段为 `Pending` | 确认 Pod 因无法启动而未运行 |

**证据说明**：K8s 状态与事件高度一致，均指向镜像拉取失败。Metric 数据佐证了 `ImagePullBackOff` 状态。日志（Logging）和追踪（Tracing）维度因工具权限问题（Forbidden）且容器未启动而无法获取，但 K8s 底层网络错误已充分诊断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效域名 registry.invalid → 节点 DNS (127.0.0.53:53) 解析失败 → 镜像拉取请求因 no such host 失败 → ImagePullBackOff
```

### 根因结论

已确认根因为 Pod 配置了无效镜像仓库域名 `registry.invalid`，导致 Kubelet 无法解析并拉取镜像。证据编号 [2] 中的错误详情 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` 直接证实了网络层解析失败是导致 `ImagePullBackOff` 状态的根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 12.7s
├─ 并发证据采集: 49.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 49.4s (Evidence 41.2s, RCA 8.1s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
