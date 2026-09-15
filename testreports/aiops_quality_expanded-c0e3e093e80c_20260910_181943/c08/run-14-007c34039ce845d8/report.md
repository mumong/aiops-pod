## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | `container="app", reason="OOMKilled"` | 提供致命异常的直接事实 |
| 2 | K8s State | `container.resource_limit.memory` | `container="app", value="64Mi"` | 确定受限资源的绝对阈值 |
| 3 | K8s Event | `event.message` | `Warning  BackOff ... Back-off restarting failed container app ... OOMKilled` (共 198 次, 持续 55m) | 展示故障的持续性与集群侧的反应 |
| 4 | K8s State | `container.last_exit_code` | `container="app", exit_code=137` | 证实被内核 OOM Killer 强杀的系统级状态码 |
| 5 | Logging | `log.message` | 模式：`http_request ... "memory allocation advanced"`；`allocated_mib` 在观察窗口内从 `14` 增长至 `48` (14.0~48.0) | 暴露应用进程在申请内存时逼近崩溃边缘的行为 |
| 6 | Tracing | `deepflow / l7_flow` | 对 `/work` 的 GET 请求响应码 200，时间范围 `2026-09-10 22:28` 至 `06:52` | 确认异常发生时的流量背景及请求处理路径 |

**证据印证说明**：
1. Kubernetes 侧的 `OOMKilled` 终止原因与 `137` 退出码（证据 1、4）提供了硬性的故障定性，排除了应用内部逻辑错误导致退出的可能。
2. `64Mi` 的内存硬性限制（证据 2）构成了引发该异常的客观条件。
3. 应用日志（证据 5）显示的内存分配递增过程，为为何在有限的 `64Mi` 配额下触发 OOM 提供了直接的逻辑支撑。
4. K8s 事件（证据 3）确认了该异常在较长窗口期内的复发，与日志记录的时间点及 Tracing（证据 6）中的请求处理活动相吻合。

## 🎯 根因分析 · g1

### 因果链
```text
容器内存硬限制配置过低 (64Mi) → 处理 HTTP /work 请求时内存分配逼近并突破该上限 → 触发 OOMKilled (Exit Code 137) 强杀 → 进入 CrashLoopBackOff 循环
```

### 根因结论
**已确认根因**：容器 `app` 的内存资源限制（Limit）配置为 `64Mi`（事实 2），该阈值过低不足以支撑应用在处理 HTTP 请求时的内存分配需求。日志中记录的 `memory allocation advanced` 过程及从 `14Mi` 增长至 `48Mi` 的观测值（事实 5）证明应用存在正常的内存增长行为，当该增长触及 `64Mi` 物理硬限制时，触发操作系统内核的 OOM Killer 机制，导致容器以 `137` 状态码被终止（事实 1、4），进而引发 K8s 侧的 `CrashLoopBackOff` 重启风暴（事实 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 13.1s
├─ 并发证据采集: 563.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 563.6s (Evidence 556.0s, RCA 7.5s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
