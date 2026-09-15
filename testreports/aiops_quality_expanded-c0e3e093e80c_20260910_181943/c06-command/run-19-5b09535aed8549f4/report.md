## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | 容器启动命令指定的可执行文件 /opt/app/unavailable-command 在镜像中不存在，导致进程以 Exit Code 127 崩溃并反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | ContainersReady=False, reason=ContainersNotReady | 确认应用容器当前未就绪，无法提供业务服务 |
| 2 | K8s State | container.waiting_reason | CrashLoopBackOff | 明确容器当前处于反复重启的异常状态 |
| 3 | K8s State | container.waiting_message | back-off 5m0s restarting failed container=app pod=workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6) | 展示 Pod 因重启失败导致的等待行为 |
| 4 | K8s State | container.last_terminated_reason | Error | 容器上一次异常退出的根本原因分类 |
| 5 | K8s State | container.last_exit_code | 127 | 精确的退出码，指示命令未找到 |
| 6 | K8s Event | event.message | Warning BackOff 3m15s (x94 over 23m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6) | 验证在长周期内反复出现 BackOff 事件 |
| 7 | Logging | elasticsearch | sh: exec: line 0: /opt/app/unavailable-command: not found | 核心证据，直接显示可执行文件缺失并导致进程崩溃 |

**证据说明**
Kubernetes 状态数据（#2, #4, #5）结合日志事实（#7），构成了完整的故障闭环。退出码 127 直接对应 `not found` 的系统调用错误，证实了是进程启动阶段因文件缺失而立即终止；而 Waiting 状态（#3）及 BackOff 事件（#6）则是该终止原因导致的系统级反馈现象。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动命令指定的可执行文件 /opt/app/unavailable-command 在镜像中不存在 → 进程启动失败并返回 Exit Code 127 → 容器崩溃触发 K8s 重启策略 → 进入 CrashLoopBackOff 反复重启状态
```

### 根因结论

已确认根因为**应用镜像中缺失启动命令指定的可执行文件 `/opt/app/unavailable-command`**。

该事实由以下证据链条确凿支撑：
1. **直接错误日志**：系统日志明确返回 `sh: exec: line 0: /opt/app/unavailable-command: not found`，精准定位了缺失的文件路径。
2. **系统级状态印证**：Pod 退出码为 127，符合 Linux 中“命令未找到”的标准系统行为；容器状态呈现 `CrashLoopBackOff`，符合因启动即崩溃导致的反复重启特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.1s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-v08/workload: 40.0s (Evidence 31.6s, RCA 8.3s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
