## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器启动即崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (fact_id: fact-13cb3242823d) | 记录最后一次崩溃的直接原因：执行了镜像中不存在的文件 |
| 2 | K8s State | kubernetes | Container `app` exit_code: 127 (fact_id: fact-309e4ff685a5) | 证实启动命令因“命令未找到”失败，与 Logging 中的 `not found` 逻辑一致 |
| 3 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact_id: fact-aedfb62114bc) | 证实 Pod 因反复崩溃进入 CrashLoopBackOff 状态，处于 51 分钟的持续故障窗口 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 14 (fact_id: fact-4f7bd00cd9b1) | 证实故障为高频重复性事件，与 Event 记录的 BackOff 阶段相符 |

**证据说明：**
Logging 中记录的 `not found` 错误与 K8s State 中的 Exit Code 127 完美对应，共同指向同一个执行失败机制（Command not found）。Metric 中的重启计数 14 次印证了该故障是自 Pod 运行以来的高频现象，而非偶发事件。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置引用了镜像中不存在的文件 `/opt/app/unavailable-command` → 
Shell 执行 `exec` 失败，返回 Exit Code 127 → 
容器启动即崩溃，kubelet 触发 BackOff 重启策略 → 
Pod 进入 CrashLoopBackOff 状态，日志报错 not found
```

### 根因结论

**已确认的根因：** Pod 容器 `app` 的启动命令（Command）配置引用了镜像中不存在的可执行文件 `/opt/app/unavailable-command`。

**结论说明：** 
该命令配置错误直接导致容器启动失败（Exit Code 127）。日志 `not found` 与退出码 127 相互印证，确凿表明失败原因是执行文件缺失，而非资源耗尽或配置错误等其他原因。证据链完整，足以支持该根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 16.6s
├─ 并发证据采集: 37.5s
│  └─ g1 aiops-case-v08/workload: 37.5s (Evidence 27.1s, RCA 10.3s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
