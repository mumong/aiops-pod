## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff (31次重启)，当前状态为 Running (可能为最后一次重启后的短暂运行或稳定态，但日志显示其处于运行中且健康探针持续触发失败导致的重启循环边缘)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-45a115d0d714` | `pod.status: Running` | 症状：容器最近一次启动处于 Running 状态。 |
| 2 | K8s State | `fact-28c98082bfe4` | `container.last_exit_code: 137` | 症状：异常终止代码，由 OS 信号引起。 |
| 3 | K8s Event | `fact-022cd7b56f87` | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` | 因果候选：Liveness Probe 请求超时。 |
| 4 | K8s Event | `fact-b4ce8b57de7f` | `Back-off restarting failed container` (4m5s 内 x342) | 症状：进入 CrashLoopBackOff 重启循环。 |
| 5 | Metric | `fact-9da3b468225d` | `kube_pod_container_status_restarts_total: 31` | 症状：累计重启次数。 |
| 6 | Metric | `fact-4109a509a079` | `kube_pod_container_status_waiting_reason: 1` (Reason: CrashLoopBackOff) | 症状：容器当前处于等待重启状态。 |
| 7 | Logging | `fact-37cc09468761` | `10.2.0.50 - - [14/Sep/2026 14:24:28] "GET /ready HTTP/1.1" 200 -` | 现象：应用 /ready 端点响应迅速且成功。 |
| 8 | Logging | `fact-14c1dcdc42bd` | `10.2.0.50 - - [14/Sep/2026 14:24:43] "GET /ready HTTP/1.1" 200 -` | 现象：应用 /ready 端点持续响应。 |
| 9 | Tracing | `fact-3ea3501d7874` (聚合) | `L7 flow: GET /health -> 200`, Duration: min `3000632.0us` (约 3s) | 关键证据：/health 端点处理耗时约 3s。 |

**证据关联与冲突说明：**
*   Tracing (证据 #9) 显示 `/health` 请求耗时约 3s，而 K8s Event (证据 #3) 报错 `context deadline exceeded`，表明超时时间小于 3s。
*   Logging (证据 #7, #8) 显示应用本身并未挂死（/ready 响应正常），但 `/health` 的慢速处理被 Kubelet 判定为不健康。
*   K8s State (证据 #2) 的 Exit Code 137 是由 Kubelet 发送 SIGKILL（探针超时后的强制停止）导致的，而非 OOM。

## 🎯 根因分析 · g1

### 因果链
```text
Liveness Probe timeoutSeconds 设置值小于 3s（推测为 1s） → 探测请求 /health 超时 (3s > timeout) → Kubelet 判定探针失败并发送 SIGKILL (Exit 137) → Pod 进入 CrashLoopBackOff
```

### 根因结论
已确认的根因是 **Liveness Probe 配置不当**。

*   **探测机制失效**：Kubelet 配置了较短的 `timeoutSeconds`（结合事实推断约为 1s），而应用 `/health` 端点执行需要固定约 3s（证据 #9，Tracing 聚合记录 min 耗时 3000632us）。
*   **直接原因**：探针请求因 `context deadline exceeded` 超时被中断，Kubelet 将其视为容器不健康并执行 `SIGKILL`，导致容器以 Exit Code 137 终止（证据 #3、#2）。
*   **结果**：容器反复重启，形成 CrashLoopBackOff 状态（证据 #4、#6）。

当前证据不足以确认 Memory Limit（64Mi）是否为根本因素，但 Exit 137 在 Probe 超时的强相关性下，更直接地指向了探针机制而非 OOM。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 27.3s
├─ 并发证据采集: 555.1s
│  └─ g1 aiops-case-v17/workload: 555.1s (Evidence 541.4s, RCA 13.5s)
└─ 汇总总结: 15.3s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
