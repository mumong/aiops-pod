## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod配置中引用的镜像域名'registry.invalid'无效，集群DNS无法解析该主机导致镜像拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `phase: Pending`, `ContainersReady: False (ContainersNotReady: [app])` | 确认 Pod 整体状态停滞在 Pending，且容器未就绪 |
| 2 | K8s Event | kubelet (event.message) | `Failed ... Error: ImagePullBackOff` (x6) | 确认 kubelet 在拉取容器镜像阶段持续失败 |
| 3 | K8s Event | kubelet (event.message) | `Error: ErrImagePull` (x4) | 提供早期拉取失败的直接线索 |
| 4 | K8s Config | event.message / container.waiting_message | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 指明具体的失败镜像及 Registry 地址 |
| 5 | K8s State | container.waiting_reason | `reason: ImagePullBackOff` | 锁定容器当前的等待原因为镜像拉取退避 |
| 6 | K8s Event | kubelet (event.message) | `dial tcp: lookup registry.invalid ... no such host` | 提供底层网络原因：DNS 解析失败，直接验证域名无效 |

**证据关联说明：**
证据 1、2、3、5 与 6 共同构成完整的异常链路：Pod 卡在 Pending 阶段（证据 1），Kubelet 报告镜像拉取失败（证据 2、3），具体原因为 DNS 解析 `registry.invalid` 失败（证据 6），最终导致容器进入 `ImagePullBackOff` 状态（证据 5）。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用无效域名 'registry.invalid' → DNS 解析失败 (lookup no such host) → 镜像拉取失败 (ImagePullBackOff) → Pod 卡在 Pending 阶段 (ContainersReady: False)
```

### 根因结论
已确认的根因是 **Pod 配置中引用的镜像域名 `registry.invalid` 无效**。
该无效域名导致集群 DNS 解析失败（证据 6），进而使得 kubelet 无法拉取镜像 `registry.invalid/aiops/workload:missing`（证据 2、3、4），最终导致 Pod 持续处于 `Pending` 且容器进入 `ImagePullBackOff` 状态（证据 1、5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.0s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 45.0s (Evidence 40.5s, RCA 4.5s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
