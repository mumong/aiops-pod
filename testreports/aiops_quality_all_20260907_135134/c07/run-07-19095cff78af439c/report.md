## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | Error | Pod aiops-case-07/workload-dff5cbc6b-fkzvn处于CrashLoopBackOff状态，容器反复重启并返回HTTP 500错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet` / `kubernetes` | `container.waiting_reason`: `CrashLoopBackOff`; `container.last_terminated_reason`: `Error` | 确立 Pod 的故障状态与重启行为 |
| 2 | K8s State | `kubernetes` | `container.last_exit_code`: `78` | 提供容器终止的直接返回值线索 |
| 3 | K8s Event | `kubelet` | `Warning BackOff 2m39s (x42 over 12m)` | 证实重启策略生效且集群正在退避 |
| 4 | Logging | `elasticsearch` | Pattern: `CONFIG_MISSING` (status: 500); 时间窗口 `2026-09-07T14:35:33Z` 至 `14:46:54Z` | 明确报错原因为配置缺失，指向应用内部逻辑 |
| 5 | Tracing | `deepflow` / `tempo` | Flow: `GET /work` 返回 `500` (`src_ip`: 172.16.104.27 → `dst_ip`: 172.16.104.7); Trace: `b3559561ac9acd05071836e31ce2b090` | 网络层确认服务请求被接受后处理失败，与日志及应用状态一致 |
| 6 | K8s State | `kubernetes` | `container.restart_count`: `7` | 量化 Pod 异常持续时间与频率 |

**证据说明：**
K8s 状态层证实容器反复退出（状态码 78）并进入 CrashLoopBackOff。日志聚合层（#4）给出了核心诊断：应用在处理请求时因 `CONFIG_MISSING` 显式报错退出。追踪层（#5）确认了该故障在网络侧表现为 HTTP 500 错误。K8s 指标与事件数据（#3, #6）验证了集群层面对该异常重启行为的观测。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 应用捕获异常并终止进程 (exitCode=78) → Kubelet 触发重启策略 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：应用启动或运行过程中检测到关键配置缺失（`CONFIG_MISSING`），导致进程主动以退出码 `78` 终止（证据 #4, #2）。

**影响机制**：Kubernetes 检测到容器非正常退出后，依据重启策略反复拉起容器（证据 #1, #3, #6），最终因连续失败进入 `CrashLoopBackOff` 状态，导致服务不可用。

**证据支持**：
- **应用层**：日志中反复出现 `CONFIG_MISSING` 错误且伴随 HTTP 500 状态码（证据 #4），配合 Tracing 中 `GET /work` 返回 500 的事实（证据 #5），证明问题出在应用逻辑而非集群基础设施。
- **集群层**：`last_terminated_reason` 为 `Error` 且 `exit_code` 为 78（证据 #2），K8s 状态准确反映了容器因内部错误被杀死的现实（证据 #1）。

**未确认项**：
- 具体缺失的配置键名（Key）或环境变量名未在日志堆栈中显示。
- 配置缺失的根本来源（是代码错误、ConfigMap 挂载失败还是配置中心不可用）需结合应用源码或配置定义进一步确认。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 28.3s
├─ 并发证据采集: 85.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 85.2s (Evidence 73.4s, RCA 11.7s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
