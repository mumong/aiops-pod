## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff，容器 app 无法就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `reason: CrashLoopBackOff`, `back-off 5m0s restarting failed container=app pod=workload-dff5cbc6b-sjvxl_aiops-case-07(5c278abe-982e-4ea1-9540-d55e1de90b26)` (fact-196faa1d779e, fact-ae1f94576889) | 确认应用容器 `app` 处于反复重启状态，由 K8s 控制平面报告。 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... kubelet Back-off restarting failed container app in pod workload-dff5cbc6b-sjvxl_aiops-case-07` (fact-c44a18504de2) | 确认 kubelet 因重启频繁已触发退避机制，佐证崩溃持续发生。 |
| 3 | K8s State | Kubernetes | `exit_code: 78` (fact-0089b70ac118) | 提供容器退出的具体错误码，指向应用层逻辑而非 OOM 或调度问题。 |
| 4 | K8s Event | Kubernetes | `Annotations: cni.projectcalico.org/podIP: 172.16.104.63/32` (fact-87c1ef1c2fba) | 确认 Pod 已成功分配网络资源，排除了 CNI 插件导致的启动失败。 |
| 5 | Logging | Elasticsearch | `pattern: CONFIG_MISSING, http_status: 500` (fact-49733d275ab8) | 核心证据，直接指出应用在处理请求时因配置缺失返回 500 错误。 |
| 6 | Logging | Elasticsearch | `occurrence_count: 8`, `time_range: 2026-09-10T20:47:10.689Z to 21:08:10.285Z` (fact-49733d275ab8) | 证实该错误模式在运行窗口内持续、高频出现，并非单次偶发。 |
| 7 | Tracing | Tempo | `GET /work` span, `http.response.status_code: 500`, `attributes: aiops.observed_mode: config_missing_exit` (fact-018605175103) | 关联日志确认 `aiops-lab-workload` 在处理 GET `/work` 请求时因 `config_missing_exit` 模式返回 500。 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 13` (fact-cfbbc3aa2f93) | 量化验证容器已重启 13 次，与 K8s 状态一致。 |

**证据关联说明：**
K8s 报告的 `CrashLoopBackOff` 状态和 `exit_code=78`（证据 1, 3）是应用崩溃的最终表象。Logging 和 Tracing 数据（证据 5, 6, 7）提供了根本原因：应用在接收 HTTP 请求（GET /work）时，因检测到配置缺失（`CONFIG_MISSING`）主动返回 HTTP 500 并退出。Tracing 的 `aiops.observed_mode: config_missing_exit` 属性与日志中的 `CONFIG_MISSING` 模式高度一致，确证了应用逻辑导致的主动崩溃，而非资源不足或系统错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码依赖的配置项缺失 (未确认具体字段) → 应用处理请求时抛出 CONFIG_MISSING 错误并返回 500 → 应用进程因退出码 78 终止 → 容器持续进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-07/workload-dff5cbc6b-sjvxl` 中的 `app` 容器处于 `CrashLoopBackOff` 状态（证据 1, 2）。根本原因在于应用代码在运行时无法获取必要的配置项，导致在处理 `/work` 请求时抛出 `CONFIG_MISSING` 错误并返回 HTTP 500（证据 5, 7）。应用进程随后以退出码 78 主动终止（证据 3, 7），引发 kubelet 不断重启容器（证据 8），最终形成循环崩溃。

**缺失的决定性事实**：
尽管根因已定位为“配置缺失”，但尚未明确具体缺失的配置项名称（unknowns）。输入数据未包含 `ConfigMap 'workload-code'` 的内容或应用期望读取的具体环境变量/文件路径，因此无法指出是哪一个具体的键（key）缺失导致了应用启动或运行失败。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 23.7s
├─ 并发证据采集: 84.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 84.3s (Evidence 75.5s, RCA 8.6s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
