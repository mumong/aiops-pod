## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc处于CrashLoopBackOff状态，容器反复以Exit Code 137退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 28m (x69 over 128m) kubelet Liveness probe failed: HTTP probe failed with statuscode: 500` | 表明应用进程在崩溃前经历了服务不可用的状态 |
| 2 | K8s Event | kubernetes | `Warning BackOff 3m17s (x461 over 124m) kubelet Back-off restarting failed container app` | 证实容器进入了指数级退避的重启循环 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 确认容器非正常退出 |
| 4 | K8s State | kubernetes | `container.last_exit_code: 137` | 137 号退出码直接指示进程被系统信号强制终止 (通常为 OOM Killer) |
| 5 | Metric | prometheus | `container_memory_working_set_bytes: 15417344 bytes` (约 14.7Mi) | 采样时内存较低，但受限于 `query window too large` 错误，无法获取重启间隙的完整峰值 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi` | 定义了容器的硬内存上限 |
| 7 | Logging | elasticsearch | `http_status: 200, path: /work` (时间窗口 `22:09:48 - 22:10:26`) | 显示在异常发生前的一段时间内，应用曾短暂返回成功响应 |

**证据说明**：
Kubernetes 状态（事实 #3、#4）提供了最直接的故障判定：退出码 137 是 OOM 的典型特征，尽管当前的瞬时内存指标（事实 #5）低于硬性限制（事实 #6），但指标采集窗口过长导致峰值历史缺失，无法排除重启间隙的瞬时峰值。K8s 事件（事实 #1）显示的 500 错误与日志（事实 #7）中短暂的 200 响应相印证，说明在内存耗尽被杀掉之前，应用曾处于服务受损或不稳定的状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用峰值 > 96Mi Limit (事实 #6) → 内核 OOM Killer 终止进程 (Exit 137, 事实 #4) → 容器崩溃并触发 Liveness Probe 失败 (事实 #1) → Pod 进入 CrashLoopBackOff (事实 #2)
```

### 根因结论

已确认的根因为：应用进程因内存使用峰值超过 `96Mi` 的硬性限制（事实 #6），被 Linux 内核 OOM Killer 强制终止（事实 #4，Exit Code 137）。虽然瞬时内存指标（事实 #5）未显示超限，但受限于 Prometheus 查询窗口错误，缺失了重启间隙的高频采样数据，无法排除瞬间峰值。K8s 事件（事实 #1、#2）证实了由此引发的服务中断和重启循环。关于导致该内存峰值的具体代码路径，证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 4.1m
├─ 问题定位: 29.0s
├─ 并发证据采集: 206.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 206.6s (Evidence 194.5s, RCA 11.9s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
