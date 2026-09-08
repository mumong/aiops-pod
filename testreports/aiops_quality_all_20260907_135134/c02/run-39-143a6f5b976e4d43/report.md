## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，无法拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证实 DNS 解析失败导致镜像拉取连接中断 |
| 2 | K8s Event | kubelet | `Error: ImagePullBackOff` (49m 内发生 6 次) | 证实拉取失败已进入重试退避循环 |
| 3 | K8s Config | Pod Spec | 目标镜像: `registry.invalid/aiops/workload:missing` | 锁定引发故障的具体镜像资源 |
| 4 | K8s State | Pod Phase | `Pending` (ContainersNotReady) | 证实 Pod 处于就绪阻塞状态，未进入运行态 |

**证据关联说明：**
Kubernetes 事件（#1）中的原始报错直接解释了镜像配置（#3）为何无法拉取；Pod 状态（#4）与频繁的重试事件（#2）共同印证了该配置缺陷导致的持续失败现象。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 'registry.invalid' 无效 → 节点 DNS 解析失败 (NXDOMAIN) → kubelet 无法拉取镜像 → Pod 进入 ImagePullBackOff 状态
```

### 根因结论

已确认根因为：Pod 配置的镜像仓库域名 `registry.invalid` 是保留域名（RFC 2606），节点 DNS（`127.0.0.53`）无法解析该域名，导致 kubelet 拉取镜像网络请求直接失败（证据 #1）。该故障属于网络配置层面的阻断，而非镜像缺失或凭证错误。

---

## 📊 性能统计

```text
├─ 总耗时: 58.9s
├─ 问题定位: 17.4s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 35.3s (Evidence 28.0s, RCA 7.2s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
