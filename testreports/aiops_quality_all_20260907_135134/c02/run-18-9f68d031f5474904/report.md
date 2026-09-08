## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod配置了无效镜像仓库域名'registry.invalid'，导致kubelet执行镜像拉取时DNS解析失败（no such host），从而引发ImagePullBackOff异常。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ErrImagePull` (fact-3e84ba066808); `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-75bc1225b038) | 捕获容器启动失败的确切机制：DNS 解析失败导致镜像拉取中断。 |
| 2 | K8s Event | kubelet | `Error: ImagePullBackOff` (fact-77e844e08c4d); `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-7c532625c12d) | 证实容器因拉取失败进入指数退避状态，确认该异常持续存在。 |
| 3 | K8s State | Pod Status | `status: Pending` (fact-31b0258e3cc7); `restart_count: 0` (fact-9531b508d356) | 确认 Pod 处于待启动挂起状态，且尚未发生过任何容器重启，状态一致。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`=1, reason=`ImagePullBackOff` (fact-c8ba79e17bc1); `kube_pod_container_status_restarts_total`=0 (fact-5c0927e59a9a) | 监控指标独立印证了 K8s 事件中的状态码与容器重启计数。 |

**证据说明**：K8s Event 中的 DNS 解析报错（fact-1, fact-2）直接指向了镜像配置问题。Pod 状态（fact-3）和 Prometheus 指标（fact-4）在状态码（`ImagePullBackOff`）和重启次数（`0`）上与事件日志完全吻合。Logging 和 Tracing 因容器未启动被标记为 `not_applicable`，无冲突数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效镜像仓库域名 'registry.invalid' → DNS 解析失败 (no such host) → 镜像拉取失败 (ImagePullBackOff) → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 配置了无效的镜像仓库域名 `registry.invalid`**。
*   **形成机制**：该域名无法在 DNS 中被解析（报错 `no such host`），导致 kubelet 无法通过 TCP 连接获取镜像清单（fact-1, fact-2）。
*   **现象映射**：此失败直接导致容器陷入 `ImagePullBackOff` 等待状态，并在 Prometheus 监控和 K8s 事件中得到独立确认（fact-3, fact-4）。

*(注：尽管系统诊断标记为已发布，但 `publication.diagnosis_publishable` 为 `false`，依据“证据不足”规则，此处仅陈述由工具事实直接支撑的因果分析。)*

---

## 📊 性能统计

```text
├─ 总耗时: 54.3s
├─ 问题定位: 17.3s
├─ 并发证据采集: 26.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 26.4s (Evidence 20.3s, RCA 6.1s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
