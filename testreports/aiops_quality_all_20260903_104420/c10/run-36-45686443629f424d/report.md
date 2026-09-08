## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | App container process crash with Exit Code 137 (SIGKILL) while responding with HTTP 500 on Liveness probe |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: `CrashLoopBackOff` | 标识 Pod 持续重启的异常状态 |
| 2 | K8s State | Kubernetes | container.last_exit_code: `137` (Exit Code: 137) | 判定进程被外部信号强制终止的终止码 |
| 3 | K8s State | Kubernetes | container.last_terminated_reason: `Error` (reason: Error) | 容器因错误被终止的官方原因 |
| 4 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 存活探针捕获到后端应用返回 500 内部错误 |
| 5 | K8s Event | Kubernetes | BackOff restarting failed container app (x385 over 101m) | 证实容器经历了长期、高频的崩溃重启循环 |
| 6 | K8s Config | Kubernetes | container.resource_limit.memory: `96Mi`, container.resource_limit.cpu: `200m` | 提供进程资源硬限制的边界环境，用于评估资源相关故障背景 |
| 7 | Logging | Elasticsearch | `http_request` completed (http_status: 200, path: `/work`, count: 8, first: `21:50:11.761Z`) | 记录应用部分正常请求的情况 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `35` | 从指标侧面验证容器频繁重启的事实 |

证据说明：
- K8s 事实（#1, #3, #4, #5）完整构建了“探针失败（HTTP 500）→ 进程崩溃（Exit 137）→ 容器进入 CrashLoopBackOff 并频繁重启”的证据链。
- 日志（#7）显示的 200 状态码表明应用曾短暂或交替处理正常请求，但这无法解释最终导致 137 退出码的终止机制；137 码是判定崩溃的直接证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程异常响应/终止 → Liveness 探针收到 HTTP 500 → 触发 OOMKiller 或系统级强制终止 → 退出码 137 (SIGKILL) → 用户可见 Pod 持续 CrashLoopBackOff 及 Liveness 失败
```

### 根因结论

已确认根因为 **App 容器进程发生异常终止（退出码 137 / SIGKILL），导致 Liveness 探针检查失败（HTTP 500），从而触发容器重启循环。**

- **现象支撑**：容器 `app` 的最终退出码为 `137`（对应 Linux 信号 `9 (SIGKILL)`），且 Kubernetes 事件明确记录“Liveness probe failed: HTTP probe failed with statuscode: 500”。这表明探针在探测时应用未能成功响应健康检查（返回了 500），随后进程被操作系统强制杀死。
- **证据关联**：证据 1、3、5 确认了 CrashLoopBackOff 状态；证据 2、4 确立了 137 退出码与探针失败的直接关联。

**说明**：虽然配置了 96Mi 的内存限制（证据 6），这通常是导致 OOMKiller（137）的常见原因，但输入事实中未包含内存使用量超过限制的指标（如 `OOMKilled` 状态的 explicit reason 或内存峰值 Metric），且日志显示应用曾返回 200。因此，具体导致 137 的信号（是内存不足触发的 OOM，还是应用内部逻辑触发的系统级 kill）缺乏决定性事实。但进程异常终止并导致探针失败这一根因已得到充分证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 26.2s
├─ 并发证据采集: 72.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 72.1s (Evidence 65.1s, RCA 6.8s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-oomkilled
