## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ErrImagePull | Pod workload-65b7f54794-rnlv4 处于 ErrImagePull/ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-65b7f54794-rnlv4` 状态 `Pending`，容器 `app` 等待原因 `ImagePullBackOff`，等待信息：`Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认容器因镜像拉取失败进入退避等待阶段 |
| 2 | K8s Event | kubernetes | `Error: ErrImagePull` 及 `Failed to pull image... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-8f74291db249, fact-bc9207409a8c) | 确证核心故障：DNS 解析失败导致网络请求中断 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 当前值为 `1`，标签 `reason="ImagePullBackOff"` (fact-67c95fc6fd9f) | 提供时序监控视角的故障佐证 |
| 4 | K8s Config | kubernetes | 容器 `app` 资源请求：CPU `5m`，Memory `8Mi`；限制：CPU `50m`，Memory `32Mi` (fact-036816c90ab2, fact-103ebf0096f6 等) | 排除资源不足导致启动失败的可能 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值为 `0` (fact-54f2b7b641f4) | 排除容器因 OOM 或健康检查失败导致的重启问题 |

**证据关联说明：**
Kubernetes 事件 (fact-bc9207409a8c) 与等待信息 (fact-059330887f5a) 共同指向镜像拉取失败，且根本原因明确为 `registry.invalid` 域名解析失败 (no such host)。Metric 数据 (fact-67c95fc6fd9f, fact-54f2b7b641f4) 提供了独立的时序佐证，确认了当前处于 ImagePullBackOff 状态且无重启记录。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了无效的镜像仓库域名 registry.invalid → 集群 DNS (127.0.0.53) 无法解析该域名 → kubelet 拉取镜像时网络连接失败 (no such host) → Pod 状态变为 ErrImagePull 并进入 ImagePullBackOff 退避等待
```

### 根因结论

已确认根因为 **Pod Spec 中配置的镜像仓库域名 `registry.invalid` 在集群内部 DNS 中无法解析**，导致容器镜像拉取失败。

- **现象印证**：Pod 处于 `ErrImagePull` 状态，且反复触发 `BackOff` 事件 [证据 #2, #3]。
- **原因确认**：Kubernetes 事件日志中直接包含 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` [证据 #2]，排除了网络策略拒绝或鉴权失败等可能。
- **环境排除**：容器资源请求量极小且未被占用，重启次数为零，证实非资源争用或运行期崩溃 [证据 #4, #5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.1s
├─ 并发证据采集: 74.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 74.3s (Evidence 66.4s, RCA 7.7s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
