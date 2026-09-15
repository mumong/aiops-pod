## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 持续处于 Pending 状态且容器处于 ImagePullBackOff，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-2675baff5594) | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing" ... Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 镜像拉取失败的直接报错，包含 DNS 解析失败的详细错误原文 |
| 2 | K8s State | kubernetes (fact-d6ee0349d4f9) | 容器 `app` 等待原因：`rpc error: code = Unknown desc = failed to pull and unpack image "registry.invalid/aiops/workload:missing"... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认容器处于因拉取镜像失败导致的等待状态 |
| 3 | Metric | prometheus (fact-0f27a5a2ed6b) | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"}` = 1 | 指标层观测到该 Pod 容器持续处于 ImagePullBackOff 状态 |

1. **证据印证**：Kubernetes 事件与状态中均明确记录了因 `lookup registry.invalid ... no such host` 导致的拉取失败，与 Metric 层观测到的 `ImagePullBackOff` 状态完全一致，共同证实了 Pod 因网络解析失败无法启动。
2. **缺失维度说明**：日志与追踪维度未获取到数据，因容器未能成功启动，物理上不存在应用进程日志或请求追踪记录。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置使用无效域名 'registry.invalid' → 节点 DNS 查询失败 (no such host) → Kubelet 镜像拉取失败 (ErrImagePull) → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认根因为镜像地址配置错误。Pod 配置拉取镜像 `"registry.invalid/aiops/workload:missing"`，其中域名 `registry.invalid` 为保留的无效测试域名，导致节点 DNS 解析彻底失败（见事实 #1、#2）。Kubelet 无法连接仓库拉取镜像，进而触发容器回退重试进入 `ImagePullBackOff` 状态（见事实 #3）。现有 Kubernetes 事件、状态及指标证据链条完整，足以支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.1s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 44.5s (Evidence 37.1s, RCA 7.3s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
