## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod `aiops-case-v10/workload` 的容器 `app` 配置中未定义环境变量 `APP_REQUIRED_CONFIG`，导致容器启动后执行逻辑检测到变量缺失，主动以 exitCode 78 退出，引发 Kubernetes 持续重启从而处于 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: {"container": "app", "reason": "Error"} | 确认容器异常终止的具体原因 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: {"container": "app", "exit_code": 78} | 提供退出码，表明应用非系统信号强制杀死，而是主动退出 |
| 3 | K8s State | kubernetes | `pod.condition` (Ready): {"status": "False", "reason": "ContainersNotReady", "message": "containers with unready status: [app]"} | 描述当前 Pod 未就绪的异常状态 |
| 4 | K8s State | kubernetes | `container.waiting_reason`: {"container": "app", "reason": "CrashLoopBackOff"} | 描述 Pod 持续重启的调度/运行时状态 |
| 5 | K8s State | kubernetes | `container.waiting_message`: {"message": "back-off 5m0s restarting failed container=app ..."} | 确认重启退避机制已触发 |
| 6 | Logging | elasticsearch | `log.message`: "APP_REQUIRED_CONFIG environment variable is missing" (timestamp: 2026-09-11T16:11:27.203Z) | 提供核心缺失证据，解释 exitCode 78 的触发原因 |
| 7 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: {"container": "app", "reason": "Error"} (current: 1) | 独立指标印证容器终止原因为 Error |
| 8 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: {"container": "app", "reason": "CrashLoopBackOff"} (current: 1) | 独立指标印证 Pod 正处于 CrashLoopBackOff 状态 |

上述证据链中，Kubernetes 的 `last_terminated_reason=Error` 和 `exit_code=78` 提供了容器异常退出的现场状态；Logging 中的明确错误信息“APP_REQUIRED_CONFIG environment variable is missing”解释了该退出的直接逻辑原因；Metrics 从监控视角再次确认了 `Error` 终止状态和 `CrashLoopBackOff` 等待状态的持续存在。各维度事实高度一致且相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
Pod `aiops-case-v10/workload` 的容器 `app` 未定义环境变量 `APP_REQUIRED_CONFIG` → 容器启动后执行逻辑检测到变量缺失 → 程序主动以 exitCode 78 退出 → 用户可见现象：Pod 持续重启且处于 CrashLoopBackOff 状态，不可用
```

### 根因结论

已确认根因为 Pod `aiops-case-v10/workload` 的容器 `app` 配置中缺失环境变量 `APP_REQUIRED_CONFIG`。

该根因通过以下事实得到充分支持：
1.  **触发原因**：Logging 维度捕获到应用日志明确报错 `APP_REQUIRED_CONFIG environment variable is missing` [证据 #6]。
2.  **退出机制**：Kubernetes 状态显示容器以 `exit_code: 78` 终止 [证据 #2]，这通常是应用程序检测到配置错误后主动退出的表现，而非 OOM 等系统级异常。
3.  **持续现象**：Kubernetes 状态和 Prometheus 指标均显示容器处于 `CrashLoopBackOff` 状态 [证据 #4, #8]，且最近一次终止原因为 `Error` [证据 #1, #7]，符合配置缺失导致启动失败并重启的故障模型。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.3s
├─ 并发证据采集: 48.0s
│  └─ g1 aiops-case-v10/workload: 48.0s (Evidence 41.8s, RCA 6.1s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
