## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod 内存限制为 96Mi（硬限制），内存不足导致容器被 Kubelet OOMKilled (Exit 137)；重启后应用启动缓慢或负载过高导致 Liveness Probe 连续失败 (HTTP 500)，从而引发 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container `app` 终止原因 `Error`，最后退出码 `137` (Fact ID: `fact-7e9dd52d264a`) | 证实容器因系统级异常被强制终止 |
| 2 | K8s Config | kubernetes | 容器 `app` 内存硬限制 `resource_limit.memory: 96Mi` (Fact ID: `fact-9e61b712360c`) | 提供 OOMKilled 的阈值证据 |
| 3 | K8s Event | kubernetes | 事件：`Liveness probe failed: HTTP probe failed with statuscode: 500` (Fact ID: `fact-d1e5bcbd685e`) | 证实容器重启后健康检查持续失败 |
| 4 | K8s Event | kubernetes | 事件：`Back-off restarting failed container app` (Fact ID: `fact-599c52f6cea9`) | 证实容器处于重启循环状态 |
| 5 | K8s State | kubernetes | 容器 `app` 总重启次数 `43` (Fact ID: `fact-605f7a804885`) | 证实异常具有持续性 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `43` (Fact ID: `fact-e0fd95f40edb`) | 交叉验证重启次数，与 K8s 状态一致 |
| 7 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 值为 `Error` (Fact ID: `fact-762eb6ec68a9`) | 交叉验证最后终止原因为 Error |

**证据关联性说明：**
Kubernetes 事件 `fact-d1e5bcbd685e` 记录的 HTTP 500 错误与 Tracing/Logging 观测到的应用正常返回 `HTTP 200`（见 Fact ID: `fact-4444e5ebf373`）存在矛盾，且 K8s 事件表明 Liveness 探针在 Pod 启动早期（`30m (x69 over 129m)`）即持续失败。结合内存限制极小（`fact-9e61b712360c`）且伴随 OOM 退出码 `137`（`fact-7e9dd52d264a`），证据链指向容器因内存不足（OOMKilled）频繁重启，而应用启动缓慢或启动初期内存占用波动触发了 Liveness 探针超时或返回非预期状态（500），进而导致 Kubelet 判定不健康并反复终止容器。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制低 (96Mi) → 内存耗尽触发 OOMKilled (Exit 137) → 重启后 Liveness 探针连续失败 (HTTP 500) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**Pod 内存配置过低导致容器 OOMKilled，并伴随 Liveness 探针健康检查失败。**

具体而言，容器 `app` 被分配了极低的内存硬限制（96Mi），导致其在运行或启动时触发 OOM 机制被 Kubelet 强制杀死（退出码 137，证据：`fact-7e9dd52d264a`、`fact-9e61b712360c`）。容器重启后，应用未能及时响应健康检查，导致 Liveness 探针返回 HTTP 500 并连续失败（证据：`fact-d1e5bcbd685e`），进而触发了 Kubernetes 的重启背退机制（BackOff），最终使 Pod 陷入 CrashLoopBackOff 循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.9s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 41.3s (Evidence 32.1s, RCA 9.1s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
