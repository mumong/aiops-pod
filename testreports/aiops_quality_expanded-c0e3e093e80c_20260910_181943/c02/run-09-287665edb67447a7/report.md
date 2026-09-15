## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod 配置了无效的镜像仓库域名 registry.invalid（RFC 2606 保留域名），导致节点 DNS 解析失败（no such host），进而引发镜像拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed: Failed to pull image... rpc error... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-d7c49e637316) | 核心事实：直接展示 DNS 解析失败的具体错误堆栈与域名。 |
| 2 | K8s Event | kubelet | `Normal BackOff: Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-14d7e2f39458) | 辅助事实：展示拉取失败后的重试退避行为，确认非瞬时抖动。 |
| 3 | K8s State | kubelet | `container.waiting_reason: ImagePullBackOff` (fact-2f69777cfa6d) | 症状确认：Pod 处于等待拉取镜像的终态。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-be521bfd1433) | 独立印证：Metric 数据客观反映了容器处于 ImagePullBackOff 状态。 |
| 5 | K8s Event | kubelet | `Warning Failed: Error: ErrImagePull` (fact-b537ab38c55f) | 辅助事实：早期拉取失败的错误码，佐证拉取流程中断。 |
| 6 | K8s State | kubelet | `pod.status: Pending`, `containersReady: False` (fact-3f9bae7e9adb, fact-0f05fcc5af84) | 现象确认：Pod 调度成功但未就绪。 |

**证据分析**：
Kubernetes 事件 `fact-d7c49e637316` 明确指出了 `no such host` 错误，直接将异常锚定在 DNS 解析阶段；Metric 数据 `fact-be521bfd1433` 作为独立观测源，确认了等待原因的客观存在；容器状态 `fact-2f69777cfa6d` 和 Pod 状态 `fact-3f9bae7e9adb` 描述了最终症状。各维度证据指向完全一致，无冲突。

## 🎯 根因分析 · g1

### 因果链
```text
无效镜像仓库域名 registry.invalid → DNS 解析失败 (no such host) → 镜像拉取失败 (ErrImagePull) → Pod 处于 ImagePullBackOff 状态
```

### 根因结论
已确认的根因是 Pod 配置了无效的镜像仓库域名 `registry.invalid`。
该域名属于 RFC 2606 保留域名，节点 DNS 服务 (`127.0.0.53`) 无法解析，导致 kubelet 在尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时发生网络请求失败（见证据 #1）。这一网络级故障直接导致容器无法启动，进而使 Pod 进入 `ImagePullBackOff` 状态（见证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.9s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 42.6s (Evidence 38.7s, RCA 3.8s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
