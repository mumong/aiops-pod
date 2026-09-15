## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod配置了无效的镜像仓库域名registry.invalid，且集群DNS解析器172.16.104.28(127.0.0.53)无法解析该域名，导致kubelet拉取镜像失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | status: Pending | 确认 Pod 处于停滞状态，与镜像拉取异常一致 |
| 2 | K8s Event | `kubelet` | "Error: ImagePullBackOff" | 明确指示容器镜像获取失败的状态反馈 |
| 3 | K8s Event | `kubelet` | "failed to resolve reference... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host" | 捕获根本原因：DNS 解析失败，集群 DNS (127.0.0.53) 无法识别 registry.invalid |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | 1 (labels: reason=ImagePullBackOff, container=app) | 量化确认当前等待状态的触发因素为镜像拉取回退 |

**证据关联说明**：Kubernetes 事件事实 (3) 提供了最直接的失败机制（DNS 无法解析 `registry.invalid`），Metric 数据 (4) 与 K8s 事件 (2) 交叉印证了当前处于 `ImagePullBackOff` 状态。Pod 配置与状态 (1) 提供了该现象发生的环境基线。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS(127.0.0.53)无法解析无效域名(registry.invalid) → 镜像拉取失败(Head request 53 解析错误) → Pod 状态回退(ImagePullBackOff) → Pod 停滞在 Pending 状态
```

### 根因结论

已确认根因是 **Pod 配置了无效的镜像仓库域名 (`registry.invalid`)，且集群 DNS 解析器 (127.0.0.53) 无法解析该域名**。

这一配置错误直接导致 kubelet 无法获取镜像元数据（`failed to resolve reference`），进而触发镜像拉取回退机制（事实编号 3, 4）。证据链完整闭环，无需补充日志或追踪数据即可得出结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.5s
├─ 并发证据采集: 42.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 42.5s (Evidence 36.7s, RCA 5.7s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
