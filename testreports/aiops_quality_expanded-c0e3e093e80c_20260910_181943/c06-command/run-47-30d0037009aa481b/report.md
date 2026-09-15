## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload (aiops-case-v08) 处于 CrashLoopBackOff 状态，容器 app 反复启动失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff; container.waiting_message: back-off 5m0s restarting failed container=app | 确认 Pod 持续重启且已退避 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: Error; container.last_exit_code: 127 | 明确容器异常退出的具体退出码 |
| 3 | K8s Event | kubernetes | Warning BackOff: Back-off restarting failed container app in pod workload_aiops-case-v08 | 证实重启行为已被 kubelet 观测 |
| 4 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接指明进程因找不到可执行文件而崩溃 |
| 5 | K8s Config | kubernetes | container.resource_limit.cpu: 50m; container.resource_limit.memory: 32Mi | 确认容器资源限制（用于排除 OOMKill） |
| 6 | Metric | prometheus | container restart_count: 15; reason: CrashLoopBackOff | 量化容器启动失败的次数，佐证长期未解决 |
| 7 | Topology | observability-gate-1 | (无数据) | 采集失败或无匹配结果，排除拓扑层面的网络/路由异常 |

日志直接展示了容器在尝试执行 `/opt/app/unavailable-command` 时失败（Exit Code 127 是 Linux 下的标准“命令未找到”返回码），这完美解释了 K8s 状态中观察到的反复退出（Last Terminated Reason: Error）。资源配置显示 CPU/Memory 限额极低，但退出码并非 137，因此可排除因资源耗尽被 OOM Killer 杀死的场景。由于 Topology 维度无数据，暂无法进一步分析启动失败前是否有网络层面的前置依赖问题。

## 🎯 根因分析 · g1

### 因果链

```text
YAML 配置中 command 指定了不存在的路径 '/opt/app/unavailable-command' → 容器入口执行失败 (Exit Code 127) → kubelet 持续拉起并触发 BackOff → 集群显示 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：Pod 容器 Command 配置错误。**

证据（#4, #2）充分表明，`app` 容器在启动时尝试执行 `/opt/app/unavailable-command`，但操作系统返回 `not found`（即退出码 127）。K8s 根据重启策略自动尝试重启该容器，最终导致 `CrashLoopBackOff` 状态（#1, #3, #6）。该根因有直接的工具事实支持，无需进一步假设。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.6s
├─ 并发证据采集: 71.9s
│  └─ g1 aiops-case-v08/workload: 71.9s (Evidence 62.5s, RCA 9.3s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-imagepull-failed
