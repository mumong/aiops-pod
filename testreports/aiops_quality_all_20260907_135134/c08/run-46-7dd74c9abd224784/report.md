## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod workload-5c9c7b6489-wmjhr in aiops-case-08 is in Back-off restart loop with Reason: OOMKilled. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet (fact-ffb203077e57) | 容器 `app` 终止原因 `OOMKilled` | 直接定位内核杀进程机制 |
| 2 | K8s State | pod status (fact-e5c80731d6da) | `container.last_terminated_reason`: `OOMKilled` | 印证容器被 OOM Killer 终止的状态 |
| 3 | K8s State | pod status (fact-52c2ba91af02) | Exit Code: `137` | 确认进程因收到 SIGKILL 退出 |
| 4 | K8s Event | kubelet (fact-8c243514a33e) | `Warning  BackOff  88s (x497 over 129m)` | 反映应用处于高频重启且退避延长的异常循环 |
| 5 | K8s Config | pod spec (fact-ac945647916f) | `memory limit`: `64Mi` | 定义触发 OOMKilled 的资源硬性天花板 |
| 6 | K8s Config | pod spec (fact-c6a35be6bce4) | `memory request`: `24Mi` | 确认工作负载的内存起始预期 |
| 7 | Metric | Prometheus (fact-0d38adb824c5) | `kube_pod_container_status_restarts_total`: `26` | 量化应用因崩溃导致的实际重启频次 |
| 8 | Logging | Elasticsearch (fact-38359467760a) | 模式 `allocated_mib` 从 8 增长至 42 (range: 8-42) | 揭示内存占用随请求处理的持续扩张趋势 |
| 9 | Tracing | Deepflow/Tempo (fact-7b080247c4fe) | Span `GET /work` 标记 `aiops.observed_mode: oom_growth` | 从调用侧确认业务接口 `/work` 引发内存持续增长现象 |

**证据关联说明**：
K8s 层面的 `OOMKilled` (E1)、退出码 `137` (E3) 与 Metric 中的 `restarts_total: 26` (E7) 构成了完整的系统级故障闭环。日志中内存从 8MiB 增长至 42MiB (E8)，结合 Tracing 对 `/work` 接口 `oom_growth` 模式的标记 (E9)，明确了内存增长的直接诱因。当内存增长逼近并突破 `64MiB` 的 Limit (E5) 时，直接触发了前端的 `BackOff` 重启现象 (E4)。

## 🎯 根因分析 · g1

### 因果链

```text
业务接口 /work 请求导致内存持续增长(2MiB -> 42MiB) → 内存使用量逼近并超过硬限制 64MiB → 内核触发 OOMKilled 机制 (SIGKILL, Exit Code 137) → Pod 频繁重启进入 Back-off 循环
```

### 根因结论

**已确认根因：容器应用内存泄漏/持续增长超出资源硬限制。**

证据表明，应用工作负载 `workload-5c9c7b6489-wmjhr` 在处理 `/work` 请求时表现出持续的内存增长特征 (E8, E9)。其 `64MiB` 的内存硬限制 (E5) 无法容纳这种增长趋势。当内存占用超过该限制时，内核安全策略杀死了容器进程 (E1)，导致应用异常退出 (E3)。由于应用本身存在无法释放内存或需求超标的特性，Kubelet 重启容器后再次遭遇相同的内存膨胀，最终表现为高频的 `BackOff` 重启事件 (E4)。缺少具体的 RSS 历史峰值趋势数据以确认是否曾精确触顶，但 OOMKilled 状态本身已足够作为当前现象的因果证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.3s
├─ 并发证据采集: 69.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 69.6s (Evidence 57.9s, RCA 11.5s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled, pod-crashloop-runtime
