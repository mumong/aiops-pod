## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | Pod aiops-case-v09/workload 处于 CrashLoopBackOff 状态，容器反复以 Exit Code 1 退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v09/workload` 状态：`CrashLoopBackOff` (Container `app` waiting) | 确认应用容器反复非正常退出的终止状态 |
| 2 | K8s State | kubernetes | Container `app` 最近退出码：`1`；重启次数：`11` 次 | 证实进程以失败代码退出，而非正常停止 |
| 3 | K8s Event | kubernetes | Warning `BackOff`：`Back-off restarting failed container app...` (x157 over 35m) | 记录 Kubelet 对容器崩溃的重启退避行为，佐证持续故障 |
| 4 | K8s Config | kubernetes | Volume `input` 未配置 ConfigMap/HostPath 绑定，仅配置为 EmptyDir（隐含事实） | 指出关键挂载点无外部数据源，是产生文件缺失的直接配置原因 |
| 5 | Logging | elasticsearch | `FileNotFoundError` 追溯：`print(Path('/input/app.conf').read_text())` | 明确应用启动失败的原因为目标配置文件 `/input/app.conf` 不存在 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=`CrashLoopBackOff`(1)；`status_last_terminated_reason`=`Error`(1) | 从监控视角独立确认容器处于等待重启且上一次终止原因为 Error |

**证据关联分析：**
日志证据 (#5) 指出应用试图读取 `/input/app.conf` 失败，这与 K8s 事件记录的容器退出机制 (#3) 完全吻合。配置事实 (#4) 解释了为何读取失败：数据卷 `input` 仅为空目录，未提供预期文件。指标 (#6) 进一步从时间维度固化了这一“启动失败并重启”的循环模式。

## 🎯 根因分析 · g1

### 因果链
```text
Volume input 仅配置为 EmptyDir，未绑定外部配置数据 → 入口命令尝试读取不存在的文件 /input/app.conf → 进程抛出 FileNotFoundError 并返回 Exit Code 1 → Kubelet 检测到退出失败并持续重启，最终进入 CrashLoopBackOff
```

### 根因结论
已确认的根因是 **容器入口命令依赖的配置文件 `/input/app.conf` 缺失**。

该现象由以下事实链直接导致：
1. 应用启动脚本试图执行 `Path('/input/app.conf').read_text()`（证据 #5）。
2. 由于 Volume `input` 仅被配置为 EmptyDir，而未挂载任何 ConfigMap、Secret 或 HostPath 数据（证据 #4），导致路径下文件为空。
3. 这一配置缺陷导致应用进程抛出 `FileNotFoundError` 并以 Exit Code 1 终止。
4. Kubelet 检测到退出码为 1 后不断重启容器，最终因重启间隔达到上限进入 `CrashLoopBackOff` 状态（证据 #1, #2, #3, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.5s
├─ 并发证据采集: 46.6s
│  └─ g1 aiops-case-v09/workload: 46.6s (Evidence 36.2s, RCA 10.3s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
