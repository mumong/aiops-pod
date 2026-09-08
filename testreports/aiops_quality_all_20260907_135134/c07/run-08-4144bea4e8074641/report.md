## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-fkzvn 持续处于 CrashLoopBackOff 状态，无法就绪 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-dff5cbc6b-fkzvn_aiops-case-07` (Fact: fact-c8f8e0646f13) | 确认 Pod 处于 CrashLoopBackOff 状态 |
| 2 | K8s State | kubernetes | 容器退出码 `exit_code: 78` (Fact: fact-a582a40b5658) | 确定异常终止的直接数值信号 |
| 3 | Logging | elasticsearch | 日志模式 `CONFIG_MISSING` (HTTP 500, 8次) (Fact: fact-6423d1a8e1f4) | 暴露根因为应用加载配置失败 |
| 4 | Tracing | deepflow | L7 Flow `GET /work` 响应 `500` (9次) (Fact: fact-80dca9b68ddb) | 验证应用处理请求失败且持续报错 |
| 5 | Tracing | tempo | Trace `b3559561ac9acd05071836e31ce2b090` 状态码 `500`, 标签 `aiops.observed_mode=config_missing_exit` (Fact: fact-0022d2f0ccba) | 从 Trace 维度直接定位到配置缺失的终止原因 |

**证据总结**：
Kubernetes 记录表明 `app` 容器因错误 `Error` 退出（exit_code 78）且频繁重启。日志与 Trace 数据提供了决定性证据，指出应用因 `CONFIG_MISSING` 报错，这与退出事件形成因果闭环，排除了资源限制等外部因素。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的配置项缺失 → 启动/运行中加载失败返回 500 → 进程以 exitCode 78 退出 → Pod 陷入 CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因为 **应用启动或运行时因配置缺失 (`CONFIG_MISSING`) 导致异常终止**。
具体证据如下：
1.  **应用行为**：日志中出现 8 次 `CONFIG_MISSING` 错误，Trace 记录（如 `b3559561...`）中明确包含标签 `aiops.observed_mode=config_missing_exit`。
2.  **系统状态**：Kubernetes 观测到容器以退出码 `78` 终止，进而触发 `CrashLoopBackOff` 和 BackOff 重启警告。
3.  **局限性**：当前事实仅证明了是“配置缺失”导致，但未能定位到 ConfigMap `workload-code` 中具体缺失的键名或变量名。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 16.3s
├─ 并发证据采集: 128.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 128.4s (Evidence 118.2s, RCA 10.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
