## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Deployment 配置缺失 APP_REQUIRED_CONFIG 环境变量，导致容器主进程启动时主动检查失败并退出（Exit 78） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 10s (x235 over 50m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6)` | 确认异常发生持续时间，排除瞬时抖动 |
| 2 | K8s State | kubernetes | `container.last_exit_code: 78` | 证明容器启动失败退出码明确指向非 OOM 的系统级错误 |
| 3 | Logging | elasticsearch | `"APP_REQUIRED_CONFIG environment variable is missing"` | 提供直接缺失的配置事实，支撑 Exit 78 的根因 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` | 辅助验证，排除因配置过低导致 OOMKilled 的可能 |

上述证据形成闭环：`K8s Event` 证明状态长期处于 CrashLoop 模式，`Logging` 提供的缺失变量错误直接解释了 `K8s State` 中 Exit 78 的代码含义，且 `K8s Config` 中的低内存配置排除了资源耗尽导致 OOMKilled 的替代解释。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置缺失 APP_REQUIRED_CONFIG 环境变量 → 应用启动时主动检查失败 → 容器退出码 78 → CrashLoopBackOff 循环重启
```

### 根因结论

已确认的根因为 Deployment 配置缺失 `APP_REQUIRED_CONFIG` 环境变量。应用进程在启动阶段因读取不到该变量而主动执行退出逻辑（Exit 78），导致容器状态陷入 CrashLoopBackOff，并触发 Kubelet 持续的重启行为（#1, #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.1s
├─ 并发证据采集: 34.7s
│  └─ g1 aiops-case-v10/workload: 34.7s (Evidence 29.2s, RCA 5.4s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
