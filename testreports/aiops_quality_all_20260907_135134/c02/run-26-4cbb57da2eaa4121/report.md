## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置使用了保留的无效域名 'registry.invalid' 作为镜像仓库地址，导致 kubelet 在拉取镜像时 DNS 解析失败（no such host），从而引发 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-2bb1b1e70ced` | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 核心证据：镜像拉取因 DNS 解析失败直接失败，指向镜像仓库域名无效 |
| 2 | K8s Event | `fact-01c54f448351` | `Error: ErrImagePull` (x4) | 现象印证：kubelet 在 27m 内多次遭遇镜像拉取错误 |
| 3 | K8s Event | `fact-91f044df7f81` | `Error: ImagePullBackOff` (x6) | 状态确认：kubelet 进入指数退避等待状态，Pod 无法启动 |
| 4 | K8s State | `fact-679a0e22b949` | `reason: "ImagePullBackOff"` | 终态确认：容器处于 `ImagePullBackOff` 等待原因 |
| 5 | K8s State | `fact-b933b885152b` | `phase: "Pending"` | 运行状态：Pod 仍处于 Pending 阶段，未分配到容器 |
| 6 | Metric | `fact-4cf0322bd82c` | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 独立观测：Prometheus 监控确认容器等待原因确认为镜像拉取失败 |
| 7 | K8s State | `fact-04c109ccc51d` | `restart_count: 0` | 排除干扰：重启次数为 0，确认问题发生在全生命周期初期，非运行期崩溃 |

**证据综述：**
K8s 事件与监控指标（#1, #6）高度一致，共同证实 `ImagePullBackOff` 是由网络解析失败引起的；K8s 状态（#4, #5）确认了该异常的持续性；事件序列（#2 → #3）展示了从初发拉取失败到最终进入退避状态的完整过程。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库地址配置为无效保留域名 'registry.invalid' → kubelet 执行 DNS 解析 lookup 失败 (no such host) → 镜像拉取请求被拒 (ErrImagePull) → 容器进入 ImagePullBackOff 状态，Pod 滞留于 Pending
```

### 根因结论

已确认的根因是 Pod 配置中使用的镜像仓库地址 `registry.invalid` 为保留的无效域名。该域名无法通过集群 DNS (127.0.0.53) 解析（证据 #1），导致 kubelet 无法获取镜像，进而触发 `ImagePullBackOff` 状态（证据 #3, #4）。

现有证据已完全支撑上述结论。仅存的未知项在于 `registry.invalid` 是否为配置错误或有意为之的测试用例，但这不影响对当前故障现象（ImagePullBackOff）的技术归因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.8s
├─ 并发证据采集: 48.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 48.6s (Evidence 44.0s, RCA 4.5s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
