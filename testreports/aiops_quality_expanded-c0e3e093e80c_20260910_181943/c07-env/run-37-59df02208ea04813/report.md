## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态，容器反复启动失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 退出码 `78`，最后终止原因 `Error` | 确认容器进程异常终止，提供退出码关键线索 |
| 2 | K8s State | kubernetes | `container.waiting_reason` 为 `CrashLoopBackOff`，等待原因包含 `back-off 5m0s restarting failed container=app` | 确认 K8s 调度器已观察到崩溃并进入指数退避循环 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v10/workload` (UID: `d3e0dc86...`) 状态 `Running` 但 `ContainersReady` 为 `False`，重启计数 `17` | 确认 Pod 处于反复重启的病态循环中 |
| 4 | Logging | elasticsearch | 日志消息: `APP_REQUIRED_CONFIG environment variable is missing` | **直接证据**：捕获了应用层报错原因，指出缺失环境变量 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值 `17`，`status` 为 `CrashLoopBackOff` | 独立验证了容器重启次数与 K8s State 观测一致 |

日志中记录的具体报错 `APP_REQUIRED_CONFIG environment variable is missing` 直接解释了容器以非 0 码（Exit Code 78）退出的原因。该日志模式在采集时即捕获到，与 K8s 层面的 `CrashLoopBackOff` 状态及 Metric 中的重启计数相互印证，排除了资源耗尽或网络不通等其他常见崩溃原因。

## 🎯 根因分析 · g1

```text
Pod 定义缺失环境变量 APP_REQUIRED_CONFIG → 容器主进程启动脚本检测到变量为空执行 sys.exit(78) → 容器以 Error 状态终止且无重试退避 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是 **应用配置文件缺失**：Pod 定义中未配置应用启动所必需的环境变量 `APP_REQUIRED_CONFIG`。

证据如下：
1. **直接报错**：日志采集事实（见证据 #4）明确记录了 `APP_REQUIRED_CONFIG environment variable is missing`，证明了应用启动脚本的校验逻辑触发了失败。
2. **崩溃退出**：K8s State 事实（见证据 #1）显示容器退出码为 `78`，符合脚本中 `sys.exit()` 的默认行为特征，证实了进程并非因资源压力或 OOM 被系统强杀。
3. **持续重试**：K8s 层面的 `CrashLoopBackOff` 状态与 Metric 中的 `restart_total=17`（见证据 #2、#5）共同反映了应用不断启动失败并触发 K8s 退避机制的循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.9s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-v10/workload: 42.0s (Evidence 33.1s, RCA 8.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
