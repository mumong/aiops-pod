## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod workload-5c9c7b6489-wmjhr is in CrashLoopBackOff status, having restarted 17 times. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `BackOff restarting failed container app` (x277) | 确证 Pod 持续处于崩溃重启状态 |
| 2 | K8s State | `container.last_terminated_reason` | `OOMKilled` / `Exit Code: 137` | 直接指出容器是被系统 OOM Killer 终止的 |
| 3 | K8s Config | `container.resource_limit.memory` | `64Mi` | 提供容器可用的最大内存上限事实 |
| 4 | Logging | `http_request` pattern | `memory allocation advanced` 观察到内存分配从 12 MiB 增长至 46 MiB | 揭示应用在处理请求时存在持续的内存递增行为 |
| 5 | Tracing | `tempo span` | `GET /work` 标记 `aiops.observed_mode: oom_growth` | 从应用视角佐证了内存增长模式 |

**证据关联说明：**
Kubernetes 维度确证了因内存超限（OOMKilled）导致的反复重启（Evidence #1, #2, #3）；Logging 和 Tracing 维度分别捕捉到了应用处理业务请求时内存使用量递增至 46 MiB 的行为轨迹（Evidence #4, #5）。二者结合印证了内存消耗逼近 64 MiB 硬限制是导致 OOM 的直接诱因。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑内存递增 (Logging: 12MiB -> 46MiB) → 触达 64MiB 硬内存限制 (K8s Config) → OOMKiller 强制终止进程 (K8s State: 137) → Pod 崩溃并频繁重启 (K8s Event: CrashLoopBackOff)
```

### 根因结论

**已确认的根因：** 容器 `app` 被分配的硬内存限制为 `64Mi`（`fact-d5ed7fd0c12c`），而应用在处理 `/work` 请求时内存占用持续攀升，已达 `46MiB` 以上（`fact-42a0d2eca737`、`fact-4530b28bad85`）。当总内存使用量突破 `64MiB` 阈值时，kubelet 触发 OOM Killer 机制强制终止进程，导致容器以退出码 137 终止（`fact-c5424d9d51e2`），进而引发 Pod 频繁进入 `CrashLoopBackOff` 状态（`fact-2e579707a380`）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 21.5s
├─ 并发证据采集: 114.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 114.8s (Evidence 105.3s, RCA 9.4s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled
