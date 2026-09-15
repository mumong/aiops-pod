## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Container command configuration error: the command specified '/opt/app/unavailable-command' does not exist within the container image (based on python:3-alpine), resulting in immediate process termination with exit code 127. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | `container.resource_limit.cpu`: 50m, `container.resource_limit.memory`: 32Mi | 确认容器资源限制配置，排除内存/CPU超限导致的 OOMKilled 或 LKilled |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 127, `container.last_terminated_reason`: Error | 确认进程退出码 127，指向命令找不到（file not found） |
| 3 | K8s Event | kubernetes | `Warning BackOff`: Back-off restarting failed container (x165 over 36m) | 反映容器频繁重启的持续故障现象 |
| 4 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供导致退出码 127 的直接执行错误文本，精准定位到命令路径错误 |

当前指标数据（`Metrics`）因 `sample_count=1` 无法展示趋势，仅确认 `kube_pod_container_status_restarts_total` 为 11，与 K8s State 中的重启计数（12次）相互印证，表明故障处于高频重启阶段；Tracing 维度缺失，但不影响基于退出码与日志的根因定性。

## 🎯 根因分析 · g1

### 因果链

```text
容器指令配置错误(/opt/app/unavailable-command) → 镜像内命令找不到(exec error 127) → 进程立即终止(exit code 127) → CrashLoopBackOff 状态及持续重启
```

### 根因结论

已确认根因为**容器命令配置错误**。

证据链完整且闭环：
1. **日志层面**（证据 #4）：elasticsearch 记录明确显示 `exec: ... unavailable-command: not found`，证实了指定命令不存在。
2. **状态层面**（证据 #2）：K8s 反馈的退出码 `127` 精确对应于 Unix 系统中的“Command not found”错误。
3. **现象层面**（证据 #3）：BackOff 事件与重启计数（证据 #2、#3）印证了进程启动失败后的持续重试循环。
4. **资源层面**（证据 #1）：资源限制（CPU 50m / Mem 32Mi）配置较低，但鉴于进程在启动瞬间即因找不到命令而终止，可排除因资源不足导致启动缓慢或崩溃的可能。

综上，根因为工作负载定义中配置的启动命令指向了一个在当前镜像中不存在的可执行文件路径。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.5s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-v08/workload: 51.1s (Evidence 46.5s, RCA 4.5s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-imagepull-failed, pod-config-error
