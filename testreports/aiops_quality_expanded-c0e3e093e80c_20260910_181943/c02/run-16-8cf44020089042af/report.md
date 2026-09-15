## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | 镜像仓库域名 registry.invalid 无法解析（DNS resolution failure） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: ... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-032030bf5535) | 证明容器运行时无法解析目标镜像仓库域名，直接阻断镜像拉取流程。 |
| 2 | K8s State | kubelet | Pod 状态为 `Pending`，且等待原因为 `ImagePullBackOff` (fact-637f06e52aff, fact-132505d4d5d5) | 确认异常表现：Pod 处于挂起状态，且未触发重启，符合启动前网络失败特征。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 指标 `ImagePullBackOff` 值为 `1` (fact-c0c09a8f7e6d) | 从监控侧印证当前处于拉取失败重试退避阶段。 |

**证据印证说明**
Kubernetes 事件明确指出 DNS 解析失败（`no such host`）是导致镜像拉取失败的直接技术原因；状态和监控指标一致反映了由此引发的 `ImagePullBackOff` 状态。由于容器尚未启动，Logging 和 Tracing 维度无数据产出符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid 无法解析（DNS resolution failure） → kubelet 拉取镜像请求失败 → 容器启动流程终止 → Pod 状态变为 ImagePullBackOff (Pending)
```

### 根因结论

已确认的根因为镜像仓库域名 `registry.invalid` 无法解析（DNS resolution failure）。

Kubelet 在尝试拉取镜像时，向 DNS 服务器 `127.0.0.53` 发起查询失败（证据 #1），导致无法获取镜像清单；Kubernetes 控制器随后将 Pod 标记为等待状态（证据 #2, #3）。现有证据链完整，足以支持该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 55.2s
├─ 问题定位: 20.9s
├─ 并发证据采集: 26.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 26.4s (Evidence 22.6s, RCA 3.6s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
