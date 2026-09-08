## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 容器内存限制（64Mi）过低，无法承载应用运行时内存增长，导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container `app` last terminated reason: `OOMKilled`; Exit code: `137` | 证明进程是被内核强制终止，非业务异常退出 |
| 2 | K8s Event | kubernetes | `Warning BackOff 23s (x140 over 38m)`; Pod restart count: `10` | 证实容器反复崩溃并处于重启退避状态 |
| 3 | K8s Config | kubernetes | Container `app` resource limit memory: `64Mi`; request memory: `24Mi` | 确认了限制容器内存使用的硬性阈值 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` (label reason=`OOMKilled`): `1` | 独立观测确认当前终止原因为 OOMKilled |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (label reason=`CrashLoopBackOff`): `1` | 独立观测确认 Pod 处于等待/重启状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` (container=`app`): `10` | 量化重启次数，验证长期故障现象 |
| 7 | Logging | elasticsearch | Pattern: `memory allocation advanced` (HTTP 200 /work); Allocated: `10Mi` → `46Mi` (Time range: `17:02:22` to `17:02:58`) | 展示应用内存随时间推移持续增长，逼近并可能突破 64Mi 限制 |
| 8 | Tracing | deepflow | L7 Flow: HTTP GET /work (src: 172.16.104.47 -> dst: 172.16.104.42); Duration: `5697us` - `18303us` | 证明故障前服务仍在正常处理业务请求 |

证据显示：K8s 指标与日志高度印证。日志表明应用在 `17:02` 处理 `/work` 请求期间内存从 10Mi 增长至 46Mi，且服务返回 200 正常响应；紧接着 K8s 层面报告 OOMKilled（Exit 137）及随后的 CrashLoopBackOff。内存使用趋势（46Mi）已占据 64Mi 限制的大部分空间，证实资源不足导致容器被杀。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务启动并处理请求 (Trace: GET /work) → 内存持续分配增长 (Log: 10Mi -> 46Mi) → 突破资源限制 64Mi → 内核 OOM Killer 终止容器 (Exit 137) → Pod CrashLoopBackOff (x10 restarts)
```

### 根因结论

**已确认的根因**：Pod `workload-5c9c7b6489-wmjhr` 中 `app` 容器的内存限制配置（`64Mi`）过低，无法承载应用运行时的实际内存增长。
*   **现象解释**：日志（证据 #7）显示应用在正常运行期间内存持续增加（10Mi 升至 46Mi），触发了 K8s 的硬限制。
*   **结果验证**：K8s 状态（证据 #1, #2）和 Prometheus 指标（证据 #4）一致确认了 `OOMKilled` 和 `CrashLoopBackOff` 状态。
*   **闭环**：应用在处理业务请求时发生内存溢出，被系统强制终止并反复重启。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.9s
├─ 并发证据采集: 72.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 72.2s (Evidence 63.7s, RCA 8.3s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
