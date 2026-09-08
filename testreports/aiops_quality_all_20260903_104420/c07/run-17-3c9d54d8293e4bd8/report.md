## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用程序容器在启动入口脚本处因缺失配置(CONFIG_MISSING)导致初始化失败，退出码78，引发Kubernetes重启循环并最终进入CrashLoopBackOff状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确定 Pod 处于重启循环的最终状态。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: Error, `container.last_exit_code`: 78 | 确认容器非正常终止且退出码为 78。 |
| 3 | K8s Event | Kubernetes | `event.message`: Back-off restarting failed container app ... (BackOff 事件记录 112 次) | 提供 K8s 控制器层面的重试阻塞证据。 |
| 4 | Logging | Elasticsearch | Pattern: `CONFIG_MISSING` (occurrence_count: 8, 时间窗: 14:01-14:26) | 提供应用层启动/运行时的具体失败原因。 |
| 5 | Tracing | Deepflow | L7 Flow: GET /work -> 500, `src_ip`: 172.16.104.9, `dst_ip`: 172.16.104.15 (occurrence_count: 9) | 证明外部流量请求被应用层拒绝。 |
| 6 | K8s Config | Kubernetes | `container.resource_request.memory`: 24Mi, `container.resource_limit.memory`: 96Mi | 排除资源限额不足导致的 OOM Kill。 |

**证据关联说明：**
*   **状态印证**：`container.waiting_reason` (K8s State #1) 与 `kube_pod_container_status_waiting_reason` (Metric) 及 `event.message` (K8s Event #3) 一致，证实集群层面的重启循环机制已生效。
*   **因果闭合**：应用日志 (Logging #4) 明确指出 `CONFIG_MISSING`，对应的 Exit Code 78 (K8s State #2) 解释了 K8s 判定容器“Error”并触发重启的机制。
*   **流量映射**：Tracing #5 中 `dst_ip` 为 Pod IP `172.16.104.15`，与 `event.message` 中的 Pod IP 匹配，确认 500 错误是该故障下的直接网络表现。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动/运行依赖配置缺失 (CONFIG_MISSING, 证据 #4) → 进程初始化失败并返回 Exit Code 78 (证据 #2) → 容器被 K8s 判定为 Error 并触发重启逻辑 (证据 #1, #3) → 进入 CrashLoopBackOff 导致流量请求被拒绝 (500, 证据 #5)
```

### 根因结论

已确认根因：应用程序因**配置缺失 (`CONFIG_MISSING`)** 导致启动/初始化失败，进而引发 Kubernetes 的重启循环和 `CrashLoopBackOff` 状态。

**证据支撑：**
1.  **应用层失败**：日志聚合 (证据 #4) 记录了 8 次 `CONFIG_MISSING` 错误。
2.  **系统层后果**：K8s 事实 (证据 #1, #2, #3) 明确显示容器以 Error 状态退出 (Exit Code 78) 并进入 BackOff 循环。
3.  **排除资源瓶颈**：资源配置 (证据 #6) 显示内存 Request 24Mi/Limit 96Mi，未触发 OOM 相关的异常退出模式。

**未确认项：**
*   缺失的具体配置文件名称或配置内容（仅知 `CONFIG_MISSING`，无法从事实中获取具体 Key）。
*   Exit Code 78 在该特定应用中的详细定义（仅确认为非零退出）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.9s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 42.0s (Evidence 31.5s, RCA 10.3s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime, pod-oomkilled
