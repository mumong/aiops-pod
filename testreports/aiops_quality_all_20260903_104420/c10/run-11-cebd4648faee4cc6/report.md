## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | {'type': 'Normal', 'reason': 'Killing', 'message': 'Normal   Killing         29m (x4 over 31m)    kubelet            Container app failed liveness probe, will be restarted'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (Fact: fact-a43fb61e8f87) | 证实应用服务在探针访问时返回了服务端错误，直接触发重启。 |
| 2 | K8s Event | kubernetes | Killing Container app failed liveness probe, will be restarted (Fact: fact-19a27b1c646e) | 证实 kubelet 因探针失败执行了 Kill 动作。 |
| 3 | K8s State | kubernetes | container.last_exit_code: 137 (Fact: fact-e777341b36fa) | 证实容器进程以 SIGKILL 信号终止，指向系统级资源保护或强制退出。 |
| 4 | K8s State | kubernetes | container.resource_limit.memory: 96Mi (Fact: fact-acad4ec124c3) | 提供内存限制上下文，需结合系统日志判断该限制是否触发 OOM。 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1 (reason: CrashLoopBackOff) (Fact: fact-0149fdca202a) | 证实当前 Pod 处于等待重启状态。 |
| 6 | Logging | elasticsearch | http_request /work 成功 (http_status: 200)，allocated_mib 始终为 0 (Fact: fact-69e91fc27379) | 显示应用正常处理请求且未发生实际内存分配，与内存 OOM 或应用报错的预期表现存在差异。 |
| 7 | Tracing | deepflow | L7 Flow GET /work response_code: 200, dst_ip: 172.16.104.31 (Fact: fact-494877c33803) | 网络层面观测到服务对正常 GET 请求响应正常，限制了根因范围。 |

证据 1、2 证实了探针失败导致重启的直接因果链；证据 3 的退出码 137 提供了进程被杀的系统信号证据。但证据 6、7 显示应用日志和网络流量均为正常状态（200 且无内存增长），这与通常导致 137 退出的“资源耗尽”或“内部错误”表现形成矛盾，导致无法确定探针失败是由应用内部瞬时错误引起，还是探针配置或环境层面的问题。

## 🎯 根因分析 · g1

### 因果链

```text
根本原因不明：资源限制(96Mi)或Liveness Probe配置问题 → 机制：容器进程被SIGKILL终止(exitCode 137)或探针判定失败 → 直接失败：Liveness Probe返回500且容器重启 → 现象：CrashLoopBackOff
```

### 根因结论

**证据不足**。

现有证据确认了“应用进程在 Liveness Probe 检查期间被 Kill 并返回 HTTP 500”这一现象，但无法区分具体根因：
1.  **应用崩溃假说**：应用在处理 `/work` 时发生内部错误导致探针超时或返回 500。但这与证据 6、7 中显示的“同一服务期间 HTTP 200 且无异常日志”相矛盾。
2.  **资源限制假说**：96Mi 的内存限制触发了 OOM Killer（符合 Exit Code 137）。但该假说缺乏节点级别日志（如 `dmesg` 中的 OOMKiller 记录）支撑，且应用日志中的 `allocated_mib` 为 0 显示并未发生预期中的内存累积。

由于缺少上一轮崩溃容器的系统级诊断日志（`previous_container_logs`）以及节点级别的内存状态证据，当前无法确认是应用自身 Bug 还是探针机制本身的问题。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 13.1s
├─ 并发证据采集: 93.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 93.9s (Evidence 82.5s, RCA 11.2s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
