## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod 启动脚本依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中未配置该环境变量，导致应用启动即打印缺失日志并以 Exit Code 78 主动退出，触发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `CrashLoopBackOff` | 确认当前 Pod 处于启动失败并退避的异常生命周期状态 |
| 2 | K8s State | `container.last_terminated_reason` | `Error` | 表明应用容器的上一次退出并非系统信号（如 OOMKilled），而是应用层报错 |
| 3 | K8s State | `container.last_exit_code` | `78` | 确认退出码，排除常见的 1/137 等系统级异常，指向特定的应用逻辑或启动脚本行为 |
| 4 | K8s Config | `container.resource_limit.memory` | `32Mi` | 提供资源上下文；鉴于退出码 78 和错误日志，排除 OOM 导致重启的可能 |
| 5 | Logging | `elasticsearch` | `APP_REQUIRED_CONFIG environment variable is missing` | **关键证据**：直接记录缺失配置的具体错误，解释退出原因 |
| 6 | K8s Event | `event.message` | `BackOff restarting failed container` | 侧面印证启动脚本连续失败触发 kubelet 的退避重启机制 |

**证据印证说明：**
K8s 状态显示异常退出（Exit Code 78）与等待原因为 CrashLoopBackOff；日志维度的唯一事实（#5）明确指出了应用因为缺少特定环境变量而主动报错。结合退出码（#3）非系统崩溃特征（如 137），日志提供的缺失变量信息是解释这一退出码的唯一直接事实，形成完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义缺失环境变量 APP_REQUIRED_CONFIG → 应用启动脚本检查配置失败 → 打印缺失日志并主动以 Exit Code 78 退出 → 触发 K8s 退避重启 (CrashLoopBackOff)
```

### 根因结论

已确认根因：应用容器 `app` 的启动脚本强依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中未注入该变量，导致启动即失败（[证据 #5]）。该错误导致应用进程主动以退出码 78 终止（[证据 #3]），被 kubelet 识别为 Error 状态并启动退避重启循环（[证据 #1, #2, #6]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.7s
├─ 并发证据采集: 71.0s
│  └─ g1 aiops-case-v10/workload: 71.0s (Evidence 65.1s, RCA 5.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
