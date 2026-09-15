## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态，重启计数持续增加（17次） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 状态 `Waiting` (`CrashLoopBackOff`)，最后终止原因 `Error`，退出码 `78` (fact-965bfdd5a4fa, fact-3e03d1127245, fact-bc72c7f5e4e2) | 证实应用进程发生严重错误并退出，被 K8s 强制重启 |
| 2 | K8s Event | kubernetes | `Warning BackOff` 事件，`x286` 次重复，时间跨度 65m (fact-1259b2214a1d) | 证实重启频率过高且 Kubelet 已开始退避 (Back-off 5m0s)，排除瞬时故障 |
| 3 | K8s Event | kubernetes | Pod IP `172.16.104.63/32` 分配成功，Ready 状态 `False` (fact-8ef07babce13, fact-191d4c8d3d2f) | 证实网络与调度层面正常，故障位于应用容器内部 |
| 4 | Logging | elasticsearch | 模式 `CONFIG_MISSING`，`http_status: 500`，`path: /work`，发生 8 次 (fact-4c0895a0de49 等) | 直接表明应用启动或运行期间因配置缺失主动返回了 500 错误 |
| 5 | Tracing | deepflow | Flow `GET /work` -> 状态码 500，耗时 8-40ms，Trace ID `78c5df7615a0195018d603083f8c6f4b` 与日志关联 (fact-1475da77a435) | 证实 500 错误源于应用处理业务请求时，非底层网络或基础设施超时 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 17，`waiting_reason`=CrashLoopBackOff (fact-8508a725b616) | 确认重启次数与 K8s State 事实一致，且处于持续异常态 |

**证据链说明**：
Kubernetes 层面的 `CrashLoopBackOff` (事实 1, 2) 是由应用内部错误导致的。日志明确记录了 `CONFIG_MISSING` 导致 HTTP 500 (事实 4)，追踪数据验证了该 500 错误确实发生在应用处理 `GET /work` 请求的过程中 (事实 5)。应用因返回 500 导致进程异常退出 (退出码 78, 事实 1)，触发 Kubelet 的重启策略，最终演变为 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 应用业务逻辑返回 HTTP 500 (Exit Code 78) → Kubelet 容器异常退出触发重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：
应用容器 `app` 因**配置缺失**导致内部服务在接收到请求（如 `GET /work`）时抛出异常并返回 HTTP 500，进而致使进程以退出码 78 终止。由于应用缺乏自我恢复能力或健康检查逻辑触发重启，容器被 Kubelet 反复拉起并再次异常退出，最终陷入 `CrashLoopBackOff`。

**证据支撑**：
1.  **日志与追踪关联**：日志中聚合的 `CONFIG_MISSING` 模式 (fact-4c0895a0de49) 与 DeepFlow/Tempo 追踪数据 (fact-1475da77a435) 相互印证，证明 500 错误源于应用业务层而非环境资源。
2.  **K8s 状态反馈**：退出码 78 (fact-bc72c7f5e4e2) 配合 `CrashLoopBackOff` 状态 (fact-965bfdd5a4fa) 证实了应用非被动 OOM 或被杀，而是内部主动崩溃退出。

**未确认/信息不足**：
缺失具体的配置项名称（如 ConfigMap/Secret 名称或字段名）或具体的挂载路径失败原因。当前证据仅能确定错误模式为“配置缺失”，无法直接定位到配置源的物理缺失或应用读取配置的逻辑错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 12.9s
├─ 并发证据采集: 57.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 57.5s (Evidence 48.5s, RCA 8.9s)
└─ 汇总总结: 15.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
