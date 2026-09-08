## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed` Error: `lookup registry.invalid on 127.0.0.53:53: no such host` (fact-4c3ab1060e42) | 确认 kubelet 尝试拉取镜像时，DNS 解析直接失败，无法建立连接 |
| 2 | K8s Event | Kubernetes | `BackOff` 87次 (fact-67ff12bc515a) | 证明拉取动作被连续重试并进入退避策略，状态长期停滞 |
| 3 | K8s State | Kubernetes | Pod `aiops-case-02/workload-65b7f54794-rnlv4` 状态为 `Pending`，状态为 `ImagePullBackOff` (fact-77ae255ca5bb) | 描述故障的最终表现形式：容器因无法获取镜像而处于等待状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (ImagePullBackOff) 值为 1 (fact-acd6d30c1de5) | 验证当前 Pod 正处于镜像拉取失败后的等待期，与 K8s 事件互为印证 |

**证据关联说明：**
Kubernetes 事件（#1）提供了确切的错误原因：访问 `registry.invalid` 时遭遇 `no such host`，这构成了因果链的上游；Pod 的 `Pending` 状态和 `ImagePullBackOff` 现象（#2, #3, #4）是该上游原因导致的直接结果。

## 🎯 根因分析 · g1

### 因果链

```text
镜像地址 registry.invalid 为保留域名，无法解析 → DNS 解析失败 (lookup no such host) → 镜像拉取无法建立连接 → 容器陷入 ImagePullBackOff 状态
```

### 根因结论

已确认根因为：**Pod 配置使用了保留域名 `registry.invalid` 作为镜像仓库地址**。

该域名为 RFC 2606 定义的保留域名，集群 DNS 服务（127.0.0.53）无法进行解析，导致 kubelet 执行 `Head "https://registry.invalid/v2/..."` 时直接报 `no such host` 错误，进而引发 `ErrImagePull` 并最终进入 `ImagePullBackOff` 状态。这一结论得到了 K8s 事件（fact-4c3ab1060e42）中原始报错的直接支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 15.8s
├─ 并发证据采集: 63.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 63.9s (Evidence 56.0s, RCA 7.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
