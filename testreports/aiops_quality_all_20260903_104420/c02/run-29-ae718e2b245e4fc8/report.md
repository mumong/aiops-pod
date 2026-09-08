## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod spec 中配置的镜像仓库地址 'registry.invalid' 为无效域名（RFC 6761 reserved TLD），导致 kubelet 执行拉取镜像操作时 DNS 解析失败，引发 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": ... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-0850546d1666) | 证明 DNS 解析失败，无法连接镜像仓库，直接导致镜像拉取错误 |
| 2 | K8s Event | kubernetes | `Error: ImagePullBackOff` (fact-5a440f1a71ec) | 确认 Pod 最终进入不可用的 `ImagePullBackOff` 状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 1，labels 包含 `reason: ImagePullBackOff` (fact-aa18f1b273e9) | 指标侧证实 Pod 处于 `ImagePullBackOff` 状态 |
| 4 | K8s State | kubernetes | Pod status: `Pending` (fact-27605811a1c6) | 确认 Pod 调度后处于 `Pending` 阶段未转为 Running |

**证据印证说明**：
K8s 事件 `fact-0850546d1666` 中的 DNS 报错与 `fact-5a440f1a71ec` 中的异常状态直接因果关系，Metric `fact-aa18f1b273e9` 从指标维度佐证了 K8s 事件的结论，四者指向完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
镜像地址 registry.invalid 配置错误 → kubelet DNS 解析失败 (no such host) → 镜像拉取失败 (ErrImagePull) → Pod 进入 ImagePullBackOff 状态
```

### 根因结论

**已确认根因**：Pod 规范（spec）中配置的镜像仓库地址 `registry.invalid` 为无效域名（RFC 6761 保留顶级域名），导致 kubelet 执行拉取操作时无法进行 DNS 解析，进而引发镜像拉取失败并陷入 `ImagePullBackOff` 状态。

- 该结论由 K8s 事件记录（事实 1、3）与 Metric 状态（事实 4）共同证实。
- 已知未知项：`registry.invalid` 是故意配置的测试域名还是运维配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.8s
├─ 并发证据采集: 54.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 54.0s (Evidence 45.0s, RCA 8.8s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
