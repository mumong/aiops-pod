## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | 容器入口命令在启动时尝试读取挂载卷 '/input/app.conf'，但该文件不存在（仅配置了 EmptyDir 卷且无外部数据源），导致进程抛出 FileNotFoundError (Exit Code 1) 并反复崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod `aiops-case-v09/workload` 状态 `Running`，容器 `app` 退出码 `1`，重启次数 `11` | 确认 Pod 调度成功，但容器进程持续异常退出 |
| 2 | K8s State | kubernetes | 容器 `app` 等待状态 `CrashLoopBackOff`，最近终止原因 `Error` | 确认 Kubernetes 已识别启动失败并触发重启限制 |
| 3 | K8s Event | kubernetes | `Back-off restarting failed container app`，事件重复 `157` 次（37m内） | 证实启动故障具有持续性和高频复现性 |
| 4 | Logging | elasticsearch | 进程启动日志调用 `Path('/input/app.conf').read_text()`，报错 `FileNotFoundError`，终止代码 `1` | 确认为应用逻辑层面的直接崩溃原因 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total=11`，`kube_pod_container_status_waiting_reason=CrashLoopBackOff` | 从监控侧独立验证了容器频繁重启和当前等待状态 |

**证据关联说明：**
- 编号 1 和 2 通过 K8s 状态确认了容器处于“反复重启”的异常生命周期。
- 编号 4 结合 1 和 2，明确了容器崩溃的直接原因是代码尝试读取不存在的文件，排除了资源不足导致的 OOMKilled。
- 编号 3 和 5 分别从事件流和指标侧证实了该故障的持续状态，与 K8s 状态的诊断结果完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
配置卷 'input' 仅为 EmptyDir，缺少挂载的文件 '/input/app.conf' → 容器入口命令执行 `Path('/input/app.conf').read_text()` 抛出 FileNotFoundError → 进程因 Exit Code 1 退出 → K8s 触发 CrashLoopBackOff 并反复重启
```

### 根因结论

已确认的根因是**挂载卷配置与启动命令的文件依赖不一致**。

具体而言：
1. **根因**：Pod 配置卷 'input' 仅为 EmptyDir，但缺少挂载的外部文件或配置源，导致文件 `/input/app.conf` 不存在（由 **K8s Event** 和 **K8s State** 支持）。
2. **直接失败**：容器入口命令在启动时调用 `read_text()` 方法读取该文件，因 `FileNotFoundError` 导致进程立即终止，退出码为 1（由 **Logging** 支持）。
3. **现象**：Kubernetes 检测到容器频繁退出，触发 `CrashLoopBackOff` 状态并持续重试重启（由 **K8s State**、**K8s Event** 和 **Metric** 支持）。

现有证据（K8s 状态、日志堆栈、Prometheus 指标）已形成完整闭环，足以确认该故障原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.2s
├─ 并发证据采集: 46.0s
│  └─ g1 aiops-case-v09/workload: 46.0s (Evidence 37.2s, RCA 8.7s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
