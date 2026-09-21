## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed ... Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": rpc error: code = NotFound desc = failed to pull and unpack image ... not found` (fact-990635df2d36) | 直接指向镜像拉取失败的具体错误原因。 |
| 2 | K8s Event | Kubernetes | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-fc4269bcf0fe) | 确认重试退避状态。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` (fact-b1979749f25a) | 从监控维度印证当前 Pod 持续处于镜像拉取失败状态。 |

**证据互证：**
Kubernetes 事件的 `NotFound` 错误（证据 #1）与 Prometheus 监控中持续的 `ImagePullBackOff` 状态（证据 #3）相互印证，共同锁定故障为镜像查找失败，而非网络或权限类错误。

## 🎯 根因分析 · g1

### 因果链

```text
指定的容器镜像标签在远程仓库中不存在 → kubelet 拉取镜像失败并返回 code = NotFound → 容器状态持续等待并进入 Back-off 重试 → Pod 处于 ImagePullBackOff 状态且未运行
```

### 根因结论

已确认根因为：容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不存在（404 NotFound）。该错误由 kubelet 直接报告（证据 #1），且被监控指标持续确认（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 33.1s
├─ 并发证据采集: 57.6s
│  └─ g1 aiops-case-v07/workload: 57.6s (Evidence 47.7s, RCA 9.6s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
