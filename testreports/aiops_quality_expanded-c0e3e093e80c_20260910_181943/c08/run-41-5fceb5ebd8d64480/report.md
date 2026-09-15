## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Reason: OOMKilled`, `Exit Code: 137` | 直接确认容器进程被内核 OOM Killer 终止 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory` = `64Mi` | 确认存在导致终止的容器内存硬限制 |
| 3 | Logging | Elasticsearch | `memory allocation advanced`, `allocated_mib`: `14` → `46` | 展示业务请求期间内存呈步进式增长，逼近限制阈值 |
| 4 | Tracing | Deepflow/Tempo | `GET /work` (HTTP 200), `duration_us`: `10243` ~ `19332` | 验证触发内存增长的具体业务请求与调用链路 |
| 5 | K8s State | Kubernetes | `status`: `CrashLoopBackOff`, `restart_count`: `24` | 确认 OOM 频繁触发导致容器处于异常重启循环 |

上述证据形成了完整的因果闭环：Tracing 确认 `GET /work` 接口被访问，Logging 显示该接口触发内存连续增长（从 14MiB 增至 46MiB），触及 Kubernetes 配置的 `64MiB` 硬限制后，引发 OOM Killer 动作（Exit 137），最终导致 Kubernetes 状态转为 `CrashLoopBackOff`。

## 🎯 根因分析 · g1

### 因果链

```text
业务请求 /work 触发内存分配 → 内存累计消耗逼近 64MiB 硬限制 → 触发内核 OOM Killer (Exit 137) → 容器反复崩溃导致 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用内存配置不足导致 OOM 崩溃。**

应用服务在处理请求 `/work` 时执行步进式内存分配（日志观测到分配量从 14MiB 升至 46MiB），这一内存增长使得应用总占用量逼近并触及 Kubernetes 配置的 `64MiB` 硬限制（证据 #2, #3）。内存超限触发了内核机制，以 Exit Code 137 强制终止了容器进程（证据 #1）。由于该资源限制无法满足业务的实际内存峰值需求，容器在每次重启后重复触发此 OOM 事件，最终被 Kubernetes 调度器标记为 `CrashLoopBackOff`（证据 #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 25.2s
├─ 并发证据采集: 62.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 62.9s (Evidence 53.6s, RCA 9.2s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-oomkilled
