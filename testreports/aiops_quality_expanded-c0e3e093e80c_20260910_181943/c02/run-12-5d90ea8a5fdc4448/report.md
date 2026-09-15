## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ErrImagePull | Pod workload-65b7f54794-z7kdp 处于 Pending 状态，容器 app 处于 ImagePullBackOff，无法拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-22f9b9cfbcc2) | **核心因果事实**：明确显示 DNS 解析失败 (`no such host`)，直接证明镜像仓库不可达。 |
| 2 | K8s Event | Kubernetes | `Error: ImagePullBackOff` (fact-281a55526423); `Back-off pulling image...` (fact-3de1e7e4155d) | 确认故障机制：因拉取失败触发指数退避，状态由 ErrImagePull 转为 ImagePullBackOff。 |
| 3 | K8s State | Kubernetes | Pod 状态 `Pending` (fact-ddcb55d94267) | 确认当前状态：Pod 因容器无法启动而被阻塞在 Pending 阶段。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-25036fb988c0) | 监控视角佐证：量化确认容器当前处于 `ImagePullBackOff` 等待状态。 |

**证据说明**：
Kubernetes 事件中的 DNS 错误 (`no such host`) 与 `ImagePullBackOff` 状态（fact-22f9b9cfbcc2, fact-281a55526423）直接构成了完整的故障链条。Metric 数据（fact-25036fb988c0）在统计维度上独立验证了该状态的存在。Pod 未启动导致日志与追踪数据为空，属于正常限制。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 'registry.invalid' DNS 解析失败 (no such host) → kubelet 无法获取镜像 Manifest 并拉取 → 触发 ImagePullBackOff 退避机制 → Pod 保持 Pending 状态，无法启动
```

### 根因结论

已确认的根因为：**Pod 配置的镜像仓库域名 `registry.invalid` 在集群 DNS 中不可解析。**

*   **证据支撑**：
    *   关键错误原文 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-22f9b9cfbcc2) 确证了 DNS 层面找不到该主机。
    *   该解析失败导致镜像拉取失败，进而引发 `ImagePullBackOff` (fact-281a55526423)，这与 Pod 长期处于 `Pending` 状态 (fact-ddcb55d94267) 和 Prometheus 观测一致 (fact-25036fb988c0)。
    *   资源配置 (fact-024f98fb1612, fact-b9481b4d15e7) 处于正常值范围，排除因资源不足导致的调度失败；容器重启次数为 0 (fact-b2a28eafb9f2)，进一步确认问题发生在启动阶段而非运行阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 58.9s
├─ 问题定位: 18.9s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 28.6s (Evidence 21.5s, RCA 7.0s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
