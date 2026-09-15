## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `ImagePullBackOff` | 确立核心异常状态 |
| 2 | K8s Event | kubernetes | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明因域名解析失败导致拉取中断 |
| 3 | K8s Config | kubernetes | `container.image`: `registry.invalid/aiops/workload:missing` | 定位引发解析失败的根源配置 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` 值为 `1` | 独立观测到与 K8s 状态一致的等待原因 |
| 5 | K8s State | kubernetes | `pod.status`: `Pending` | 确认 Pod 因无法启动容器而阻塞 |

**证据印证与冲突分析：**
Kubernetes 状态（证据 1、5）直接反映容器卡死在 Pending 阶段；Kubelet 的 Event 记录（证据 2）给出了“no such host”的具体网络底层原因；Kubernetes 配置（证据 3）提供了该错误的配置源头（`registry.invalid`）。Prometheus 指标（证据 4）从时间序列观测角度交叉验证了当前容器正处于 `ImagePullBackOff` 状态，所有维度事实高度一致，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置无效域名 "registry.invalid" → 节点 DNS 解析失败 (no such host) → kubelet 拉取镜像被网络层阻断 → Pod 进入 ImagePullBackOff 状态
```

### 根因结论

已确认的根因是 **Pod Spec 中配置的镜像仓库域名 `registry.invalid` 无效**（证据 3）。

该配置直接导致节点执行 DNS 查询时失败，错误日志明确显示 `dial tcp: lookup registry.invalid ... no such host`（证据 2）。因为无法解析并连接镜像仓库，`kubelet` 无法拉取镜像，从而触发 `ErrImagePull`，随后系统进入指数退避重试，表现为 `ImagePullBackOff`（证据 1、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 55.0s
├─ 问题定位: 16.5s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 30.6s (Evidence 23.9s, RCA 6.6s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
