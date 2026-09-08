## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-723185630ccd) | container "app" last_exit_code: 78 | 确认应用进程以异常码退出 |
| 2 | K8s State | kubernetes (fact-ec2f759e1c15) | container "app" restart_count: 15 | 反映容器已频繁重启并进入循环状态 |
| 3 | K8s Event | kubernetes (fact-ccad46e0b05d) | Back-off restarting failed container app | 直接观测到的 Kubelet 重启失败现象 |
| 4 | Metric | prometheus (fact-07a65fca5d0a) | kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}: 1 | 监控指标确认容器当前处于等待重启状态 |
| 5 | Logging | elasticsearch (fact-5530ad007509) | `CONFIG_MISSING`, HTTP 500, path=/work | 明确日志错误信息，指出配置缺失 |
| 6 | Tracing | deepflow (fact-207c4f051754) | HTTP GET /work response_code: 500 | 流量日志印证应用对外返回 500 错误 |
| 7 | Tracing | tempo (fact-691f9bdc116f) | span GET /work, attribute `aiops.observed_mode="config_missing_exit"` | 链路属性直接关联配置缺失导致的退出机制 |

**证据分析：**
Kubernetes 状态（#1, #2）显示进程反复退出（Exit Code 78）并触发 Kubelet 的重启策略（#3），这与指标（#4）和日志（#5）中的 `CONFIG_MISSING` 错误形成闭环。追踪数据（#6, #7）从外部请求（HTTP 500）和内部属性两个维度确认了错误根源与配置缺失直接相关，且时间窗口一致。

## 🎯 根因分析 · g1

### 因果链

```text
配置键/环境变量缺失 (日志/追踪证实 CONFIG_MISSING) → 进程初始化失败退出 (Exit Code 78) → Kubelet 检测终止并尝试重启 (BackOff) → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：** 应用容器 'app' 因启动阶段缺少关键配置（`CONFIG_MISSING`）导致进程异常退出（Exit Code 78）。
这一退出行为触发了 Kubernetes 的重启策略，但由于配置问题未解决，容器在每次重启后再次快速失败，最终进入 `CrashLoopBackOff` 状态。

**证据支撑：**
- 日志明确记录 `CONFIG_MISSING` (证据 #5)。
- 追踪属性 `aiops.observed_mode="config_missing_exit"` 确认了退出原因 (证据 #7)。
- 容器反复退出和重启的状态与上述错误一致 (证据 #1, #2, #3)。

**未知项：** 虽然确认为配置缺失，但具体的缺失配置项名称、或导致配置不可用的上游原因（如 ConfigMap 未创建、Secret 挂载失败等）在现有数据中未明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.6s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 46.2s (Evidence 35.8s, RCA 10.3s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
