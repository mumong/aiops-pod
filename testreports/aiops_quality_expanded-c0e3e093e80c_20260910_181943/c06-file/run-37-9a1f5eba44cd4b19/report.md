## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | Pod aiops-case-v09/workload 处于 CrashLoopBackOff，容器反复以 Exit Code 1 退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning BackOff 4m48s (x202 over 49m) Back-off restarting failed container app | 证实容器长期处于重启失控状态 |
| 2 | K8s State | kubernetes | container.last_terminated_reason=Error | 记录异常终止原因分类 |
| 3 | K8s State | kubernetes | container.app.exit_code=1 | 确认进程非零退出 |
| 4 | K8s State | kubernetes | container.app.restart_count=14 | 量化崩溃频次 |
| 5 | K8s Config | kubernetes | container.app.resource_limit.memory=32Mi, resource_request.memory=8Mi | 排除内存超限因素 |
| 6 | Logging | elasticsearch | `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` | 锁定入口命令启动时的具体失败路径 |
| 7 | Logging | elasticsearch | `Traceback (most recent call last): ... return io.open(self, mode, buffering, encoding, errors, newline)` | 证实文件读取在 Python 标准库层级失败 |
| 8 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}` = 1 | 验证集群层面监控到的一致等待状态 |

**证据关系说明**：
1.  指标数据与 K8s 事件在组层面一致，确证 `CrashLoopBackOff` 是当前唯一可见症状（#1, #8）。
2.  容器退出码为 1 且重启频繁，证实了非正常退出（#3, #4）。
3.  日志明确指出了进程启动时读取 `/input/app.conf` 发生 `FileNotFoundError`（#6），构成了进程退出（#3）的直接因果链。
4.  K8s 配置显示资源限制正常且未被 OOMKill（#5），排除了资源争抢导致退出的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
挂载卷 /input 缺失配置文件 app.conf → Python 入口命令执行 Path('/input/app.conf').read_text() 抛出 FileNotFoundError → 进程以 Exit Code 1 异常终止 → Kubelet 触发退避重启，进入 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用配置缺失导致启动失败**。
容器入口命令在启动时尝试读取 `/input/app.conf` 配置文件，但由于该挂载卷为空或缺失对应文件，导致进程抛出 `FileNotFoundError` 并立即退出（`Exit Code 1`）[证据 #6, #7]。Kubelet 检测到进程终止后触发重试机制，随后进入 BackOff 循环 [证据 #1, #3]。

现有证据足以支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.3s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v09/workload: 41.3s (Evidence 32.4s, RCA 8.8s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
