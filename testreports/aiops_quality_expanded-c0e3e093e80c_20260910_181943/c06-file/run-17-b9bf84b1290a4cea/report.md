## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | 启动命令为一次性Python脚本尝试读取`/input/app.conf`，但该文件在EmptyDir卷中不存在（未挂载ConfigMap/Secret），导致容器以Exit Code 1异常退出并因restartPolicy=Always陷入CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | `emptyDir` 卷挂载至 `/input`，无其他卷挂载记录 | 确认 `/input/app.conf` 路径所在卷缺乏外部数据源（ConfigMap/Secret） |
| 2 | K8s State | kubernetes | `last_terminated_reason=Error`, `waiting_reason=CrashLoopBackOff` | 容器状态符合启动即异常退出的特征 |
| 3 | Logging | elasticsearch | `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` | 明确给出具体缺失文件及异常类型，直接指向配置缺失 |
| 4 | Logging | elasticsearch | `Path('/input/app.conf').read_text()` (fact-346fe73ee149) | 揭示启动命令中的具体读取动作，与日志报错形成因果闭环 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total=9` (fact-ebf484793cfd) | 提供持续失败并触发重启策略的量化观测数据 |
| 6 | K8s State | kubernetes | `container.last_exit_code=1` (fact-21d647f01d10) | 验证进程非正常退出状态，支撑 Error 归因 |

**证据关联性说明：**
1. 维度间印证：K8s 状态 (No.2) 与 Metric (No.5) 证实了“持续失败重启”的异常事实；Logging (No.3, No.4) 精准定位了导致该事实的直接原因。
2. 配置与现象闭环：K8s 配置显示挂载了空卷 (No.1)，结合日志中明确指向 `/input/app.conf` 的缺失 (No.3)，直接解释了为何启动命令执行时会报错退出 (No.4)，从而导致了后续的 CrashLoopBackOff (No.2)。

## 🎯 根因分析 · g1

### 因果链

```text
EmptyDir卷未挂载配置文件，导致`/input/app.conf`不存在 → 
启动命令执行`Path('/input/app.conf').read_text()`触发FileNotFoundError → 
进程以Exit Code 1终止，Kubernetes按restartPolicy=Always重启容器 → 
容器反复崩溃形成CrashLoopBackOff状态
```

### 根因结论

已确认的根因为**启动命令依赖的配置文件缺失**：
- 工作负载配置了 `emptyDir` 卷挂载到 `/input` 路径，但该卷未通过 ConfigMap、Secret 或 PersistentVolumeClaim 挂载任何数据（证据 No.1）。
- 容器启动时执行 Python 脚本尝试读取 `/input/app.conf`，由于文件不存在，抛出 `FileNotFoundError` 并导致退出码为 1（证据 No.3, No.4, No.6）。
- Kubernetes 在 `restartPolicy=Always` 策略下检测到容器失败并反复重启，进而表现为 `CrashLoopBackOff` 状态（证据 No.2, No.5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.4s
├─ 并发证据采集: 40.5s
│  └─ g1 aiops-case-v09/workload: 40.5s (Evidence 31.7s, RCA 8.6s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
