## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod `workload` 的 `command` 配置 `sh -c exec /opt/app/unavailable-command` 指向了容器镜像 `python:3-alpine` 中不存在的可执行文件，导致容器启动即退出（Exit Code 127）；在 `restartPolicy: Always` 策略下，kubelet 反复重启容器最终进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload` 状态: `Running`; Container `app` 状态: `CrashLoopBackOff` (`fact-ae7be68b036a`); Pod `Ready`: `False` (`fact-4c30f7224ba9`) | 确认为启动型故障，Pod 已调度但容器持续崩溃 |
| 2 | K8s Event | kubernetes | `BackOff` 事件: `Back-off restarting failed container app in pod workload...`，持续 22m 内触发 94 次 (`fact-050f471090a5`) | 表明重启频率极高，符合指数退避特征 |
| 3 | K8s State | kubernetes | 容器 `app` 最后一次退出码: `127` (`fact-21585156d66b`); 原因: `Error` (`fact-56ca2306f7ec`) | 判定为系统级 `Command not found` 错误 |
| 4 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (`fact-1f26c7f41d44`) | 提供确定性证据：指定的可执行文件路径在镜像中不存在 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 为 9 (`fact-7d94867c921a`) | 验证了重启状态，但仅单点样本无法评估长期趋势 |

**证据互证：**
Logging (`fact-1f26c7f41d44`) 明确指认了 `command` 指向的脚本路径导致 `127` 退出，与 K8s State 中的 `Exit Code 127` (`fact-21585156d66b`) 和 `CrashLoopBackOff` (`fact-ae7be68b036a`) 直接吻合。Metric 和 Event 仅佐证了重启频发的现象，未提供额外成因线索。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像 `python:3-alpine` 中缺失 `/opt/app/unavailable-command` 可执行文件 → 执行 `sh -c exec /opt/app/unavailable-command` 返回 127 错误 → 容器启动即退出 (Exit Code 127) → kubelet 按 restartPolicy: Always 策略反复重启，进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：Pod `workload` 的 `command` 配置指向了容器镜像 `python:3-alpine` 中不存在的可执行文件。

**依据**：
1. 日志证据 (`fact-1f26c7f41d44`) 显示 `sh: exec: ... /opt/app/unavailable-command: not found`。
2. K8s 状态 (`fact-21585156d66b`) 显示容器以 `Exit Code 127` 失败，符合命令未找到的特征。
3. 现象 (`fact-ae7be68b036a`) 表现为 `CrashLoopBackOff`，是由上述启动失败在 `Always` 策略下不断重试的结果。

正式 RCA 已通过事实校验并发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.2s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-v08/workload: 38.2s (Evidence 30.5s, RCA 7.5s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
