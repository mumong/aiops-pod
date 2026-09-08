## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | 容器内存请求与限制配置过低，导致应用在进行内存分配时触发 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 2m15s (x140 over 40m) kubelet Back-off restarting failed container app in pod workload-5c9c7b6489-wmjhr_aiops-case-08(cfa13c1e-da2a-4e37-8baa-ec4be4c24c35)` | 证实容器处于高频重启崩溃状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled` | 确认崩溃的直接触发原因为内存超限 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 137` | 与 OOMKilled 导致的系统强杀机制一致 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` | 确认内存硬限制配置极低，不足以支撑应用 |
| 5 | Logging | elasticsearch | 连续 8 次 HTTP 200 请求，内存分配从 `allocated_mib: 10` 持续上升至 `48` (时间窗口: 17:08:17 至 17:08:55) | 证实业务请求导致内存持续增长，逼近并突破限制 |
| 6 | K8s State | kubernetes | `restart_count: 11` | 反映 OOM 崩溃已导致容器多次非预期终止 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total: 11` | 从指标维度交叉验证了 K8s 状态中观察到的 11 次重启 |

**证据关联说明：**
证据 1、2、3、6 从 K8s 运行态证实了应用频繁因 OOMKilled 退出并被 BackOff；证据 4 明确了导致 OOM 的硬性资源限制条件为 64Mi；证据 5 提供了触发 OOM 的业务场景证据，显示内存请求随时间累积（10Mi -> 48Mi），证实 64Mi 限制不足；证据 7 通过 Prometheus 指标佐证了重启事实。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源限制配置过低 (64Mi) → 业务请求引发内存持续增长 (10Mi升至48Mi) → 触发 OOMKilled 退出 (Exit Code 137) → 容器频繁重启并进入 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存请求与限制配置过低**。

应用内存分配需求超过了配置的硬性上限（64Mi）。证据显示，在处理业务请求时，内存从 10Mi 持续消耗至 48Mi，逼近并突破 64Mi 限制导致内核 OOM Killer 强行终止进程（退出码 137）。该现象已在 K8s 状态（`last_terminated_reason: OOMKilled`）、日志（`memory allocation advanced` 趋势）及指标（`restarts_total: 11`）中得到多源一致验证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.3s
├─ 并发证据采集: 66.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 66.1s (Evidence 60.8s, RCA 5.2s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled, pod-crashloop-runtime
