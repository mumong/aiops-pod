## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器反复重启失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接揭示容器启动失败的具体原因及缺失命令路径 |
| 2 | K8s State | kubernetes | `last_exit_code: 127` | 确认进程未找到导致的启动失败特征码 |
| 3 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff` | 描述当前容器的反复重启状态 |
| 4 | K8s State | kubernetes | `container.resource_limit.memory: 32Mi` | 确认资源硬限制，排除资源耗尽因素 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 2` (trend_evaluable=true, count=2) | 独立确认容器重启趋势 |
| 6 | K8s Event | kubernetes | `Back-off restarting failed container app` | 确认 Kubernetes 调度层观察到重启失败事件 |

**证据印证说明：**
日志 (Log) 明确报告了 `/opt/app/unavailable-command` 缺失，这直接解释了为什么 Exit Code 为 127 (状态 2)，进而导致容器启动后立即崩溃。Kubernetes 状态指标（重启次数与 CrashLoopBackOff 状态）与日志记录在现象上完全吻合，证实了非资源类原因导致的启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置引用不存在命令 (/opt/app/unavailable-command) → 容器启动时 shell 执行失败 (Exit Code 127) → 容器反复退出触发 K8s CrashLoopBackOff → Pod 处于 Unready 状态
```

### 根因结论

**已确认根因：** 容器入口命令（Entrypoint）或启动命令配置错误。

Pod 配置中引用的可执行文件 `/opt/app/unavailable-command` 在容器镜像中不存在，导致容器启动瞬间失败并退出（错误码 127）。这一事实由日志记录（`not found`）与系统返回的退出码（`127`）相互确证。由于失败由配置错误引起，而非资源不足或依赖服务问题，因此根本原因已锁定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 14.4s
├─ 并发证据采集: 81.8s
│  └─ g1 aiops-case-v08/workload: 81.8s (Evidence 74.5s, RCA 7.2s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
