## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，容器持续重启且未就绪 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff (app) | 确认 Pod 处于反复重启状态 |
| 2 | K8s Event | kubernetes | Warning Liveness probe failed: HTTP probe failed with statuscode: 500 (x30 over 39m) | 证明探针探测目标返回了 500 错误 |
| 3 | K8s State | kubernetes | container.last_terminated_reason: Error; exit_code: 137 | 确认容器被强制终止，无核心转储 (OOMKilled 除外) |
| 4 | K8s Event | kubernetes | Normal Killing ... Container app failed liveness probe, will be restarted | 证实 kubelet 因探针失败发起终止动作 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason (reason: CrashLoopBackOff, value: 1) | 指标层面验证容器当前等待原因 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total (value: 15) | 量化重启次数，排除单次偶发错误 |
| 7 | Tracing | deepflow | HTTP GET /work 9 次，response_code: 200, dst_ip: 172.16.104.34 | 确认业务流量访问该 IP 时响应正常 |

**证据说明：**
1.  **探针与终止的因果关联**：事实 #2 (Liveness probe 500 错误) 与事实 #3、#4 (Exit Code 137/Killing) 形成直接因果闭环，说明 kubelet 探测失败后执行了强制终止。
2.  **应用行为异常**：事实 #1 (CrashLoopBackOff) 和事实 #5、#6 (重启 15 次) 确认了故障的持续性，且非瞬时网络抖动。
3.  **探测目标与业务流量的矛盾**：事实 #7 显示业务正常访问 `172.16.104.34` 返回 200，这与事实 #2 (探针返回 500) 存在冲突，提示探针探测的端点、状态或时间可能与常规业务访问路径/状态不一致。

## 🎯 根因分析 · g1

### 因果链

```text
应用端点响应 500 (疑似/探针路径) → kubelet Liveness Probe 失败 (HTTP 500) → kubelet 执行 Killing (SIGKILL, Exit 137) → 容器重启并触发 CrashLoopBackOff
```

### 根因结论

**根因：** 应用服务（container `app`）的 Liveness Probe 端点返回 `HTTP 500` 错误，导致 kubelet 判定容器不健康并执行强制终止，进而引发容器反复重启（CrashLoopBackOff）。

**证据支持：**
1.  **核心触发**：事实 #2 明确记录 Liveness probe 返回 `statuscode: 500`，这是直接违反探针逻辑（通常要求 2xx/3xx）的原因。
2.  **执行结果**：事实 #3 (Exit 137) 和事实 #4 (Killing) 证实了 kubelet 因探测失败执行了终止动作。
3.  **状态一致性**：事实 #1 (K8s State) 和事实 #5 (Metric) 均一致确认当前状态为 `CrashLoopBackOff`。

**证据局限性（关于 500 来源）：**
现有证据（事实 #2）证明探针失败，但事实 #7 (Tracing) 显示业务流量访问相同 Pod IP (`172.16.104.34`) 的路径 `/work` 返回 `200`。这表明：
*   Liveness Probe 可能配置了与业务访问不同的路径（如 `/health` 而非 `/work`），且该路径存在内部错误；
*   或者探针触发时的应用内部状态与常规业务请求时的状态不同。
但就故障表现（CrashLoopBackOff）而言，**Liveness Probe 返回 500 导致容器被杀**这一因果链已得到 K8s 事件和指标的直接证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.8s
├─ 并发证据采集: 65.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 65.2s (Evidence 57.2s, RCA 7.8s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
