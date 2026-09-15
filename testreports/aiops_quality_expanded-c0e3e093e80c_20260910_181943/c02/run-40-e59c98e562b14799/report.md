## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-290ef9edeec7) | 根本原因：DNS 解析失败，节点无法连接镜像仓库 |
| 2 | K8s Event | kubernetes | `Error: ErrImagePull` (fact-f32ba1c13ac9)、`Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-7a79917fc68e) | 机制确认：Kubelet 拉取镜像失败并触发重试退避 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-9b889df21656) | 现象佐证：容器当前正处于镜像拉取等待状态 |
| 4 | K8s State | kubernetes | `pod.status: Pending`, `container.restart_count: 0` (fact-637176a63a51, fact-c0fd076caccc) | 现象佐证：Pod 停留在 Pending 阶段，尚未分配资源，未发生过启动尝试 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi`, `cpu: 50m` (fact-12fc5a8a8258, fact-fbf097890f3c) | 排除背景：资源配置极低，排除了资源限制导致拉取失败的可能 |

Kubernetes Event (fact-290ef9edeec7) 明确记录了 DNS 查询失败的具体错误信息，与 K8s Event 中的 `ErrImagePull` 及 Metrics 中的 `ImagePullBackOff` 状态形成闭环，确证故障点在于镜像域名的不可达性。

## 🎯 根因分析 · g1

```text
镜像配置了无效域名 registry.invalid/aiops/workload:missing → 集群 DNS 解析失败 (no such host) → Kubelet 拉取镜像报错 ErrImagePull 并进入 BackOff → Pod 状态维持 Pending，容器状态为 ImagePullBackOff
```

### 根因结论

已确认的根因是 Pod 配置了无效的镜像域名 `registry.invalid`。Kubelet 在尝试拉取镜像时，DNS 系统无法解析该域名，导致底层网络请求失败并上报 `no such host` 错误 (fact-290ef9edeec7)。这一失败阻止了镜像的下载，使得 Pod 容器无法启动，进而表现为 `ImagePullBackOff` 状态 (fact-9b889df21656, fact-f32ba1c13ac9)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.7s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 36.8s (Evidence 28.0s, RCA 8.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed
