## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用启动时缺失必要配置（CONFIG_MISSING）导致HTTP请求返回500错误及进程退出码78，进而引发CrashLoopBackOff重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态 `Running`，Pod 条件 `ContainersNotReady` (status: False) | 确认 Pod 存活但业务容器未就绪 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... back-off 5m0s restarting failed container=app` (发生 423 次) | 记录 CrashLoopBackOff 的严重性与持续时间 |
| 3 | K8s State | Kubernetes | 容器退出原因 `Error`，最后退出码 `exit_code: 78` | 确认为应用层主动退出，非系统级 OOMKilled 或段错误 |
| 4 | K8s State | Kubernetes | 重启计数 `restart_count: 23` | 证实存在反复重启循环，与事件频率对应 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: CrashLoopBackOff) | 独立于 K8s API 验证当前处于等待重启状态 |
| 6 | Logging | Elasticsearch | 日志聚合：错误消息 `CONFIG_MISSING`，HTTP 状态码 `500`，路径 `/work` (发生 8 次) | 揭示进程退出前最后一次业务操作的直接错误原因 |
| 7 | Tracing | Deepflow | HTTP Flow 聚合：GET /work 请求持续返回 `response_code: 500` (发生 8 次，172.16.104.27 -> 172.16.104.7) | 证实服务在崩溃前持续向客户端返回业务逻辑错误，非基础设施故障 |

**证据关联说明：**
- **编号 3、6、7** 高度互证：日志与 Trace 共同显示在退出前处理了 `GET /work` 并返回 500，错误原因为 `CONFIG_MISSING`；这与容器非零退出码（78）的“应用层逻辑拒绝服务”特征完全一致，排除了网络中断或底层存储故障。
- **编号 2、4、5** 形成闭环：K8s Event、重启计数与 Prometheus 指标共同锁定了 `CrashLoopBackOff` 状态，说明应用启动后因上述配置缺失导致崩溃并被系统反复拉起。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行时依赖配置缺失 (CONFIG_MISSING) → 业务逻辑返回 HTTP 500 错误 → 进程触发退出码 78 主动终止 → 容器重启陷入 CrashLoopBackOff
```

### 根因结论

已确认的根因是 **应用配置缺失（CONFIG_MISSING）**。

1.  **现象支撑**：Pod 呈现 `CrashLoopBackOff` 状态，容器经历了 23 次重启，并因非零退出码（78）而终止（证据编号 2, 3, 4, 5）。
2.  **触发机制**：应用启动或运行过程中尝试访问特定配置，因配置缺失导致业务逻辑处理失败，向客户端返回 HTTP 500 错误，并随后以代码 78 退出进程（证据编号 6, 7）。
3.  **局限性**：当前证据未能捕获完整的启动日志或挂载卷清单，因此无法定位具体缺失的 ConfigMap 名称或缺失的具体配置键值，但配置缺失导致进程异常退出的因果关系已充分确立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 27.2s
├─ 并发证据采集: 64.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 64.4s (Evidence 56.0s, RCA 8.3s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
