## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod 'workload' 在 aiops-case-v08 namespace 中配置了无效的入口命令 (sh -c exec /opt/app/unavailable-command)，该命令在容器镜像 xnet.registry.io:8443/observability/python:3-alpine 中不存在，导致进程以 exit code 127 崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app in pod workload...` (fact-886553f61d64) | 确认 Pod 反复重启且 kubelet 正在退避 |
| 2 | K8s Config | Kubernetes | `sh -c exec /opt/app/unavailable-command` (诊断结论事实) | 指出导致进程无法启动的入口配置错误 |
| 3 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (fact-13cb3242823d) | 直接记录命令执行失败，证实文件缺失或不可执行 |
| 4 | K8s State | Kubernetes | `exit_code: 127` (fact-0b3a210a666d) | 提供确凿的失败退出码，与“命令未找到”机制完全对应 |

证据表明，日志中的 `not found` 错误与容器退出码 `127` 相互印证，结合 Kubernetes 事件中的 `BackOff` 状态，完整闭环验证了入口命令配置错误导致的 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
入口命令配置错误 (/opt/app/unavailable-command 文件缺失) → 进程启动失败 (Exit 127) → 触发 CrashLoopBackOff 重启 → Pod 无法就绪
```

### 根因结论

已确认根因为**容器入口命令配置错误**。Pod 配置了不存在的命令 `/opt/app/unavailable-command`，导致容器进程启动即失败（Exit 127），进而触发 Kubernetes 的重启机制进入 CrashLoopBackOff 状态。该结论由日志事实（fact-13cb3242823d）、退出码状态（fact-0b3a210a666d）及 K8s 诊断结论充分支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.1s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-v08/workload: 39.4s (Evidence 30.9s, RCA 8.4s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
