## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | {'container': 'app', 'reason': 'CrashLoopBackOff'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet` | `back-off 5m0s restarting failed container=app` (事实 fact-c349bff51573) | 确立 Pod 进入 CrashLoopBackOff 的客观状态 |
| 2 | K8s State | `kubelet` | `exit_code: 78` (事实 fact-594c1defec81) | 提供应用终止的直接返回值，指向异常退出机制 |
| 3 | Logging | `elasticsearch` | `CONFIG_MISSING` 错误模式，重复 8 次，伴随 `http_status: 500` (事实聚合事实) | 暴露应用启动时的核心业务异常，定位到具体缺失的配置标识 |
| 4 | Tracing | `tempo` | `GET /work` 请求返回 `status_code: 500`，Span 属性标识 `aiops.observed_mode: config_missing_exit` (事实 fact-018605175103) | 验证了 500 错误是由应用自身逻辑触发的配置缺失，而非网络或网关故障 |
| 5 | K8s State | `Pod Spec` | 资源配置：`limit.memory: 96Mi` (事实 fact-ccafb1462531) | 排除因内存硬限制不足导致 OOMKilled 的可能性 |

**证据印证分析**：
*   容器处于 CrashLoopBackOff 状态（#1），其核心诱因是应用启动过程中连续抛出 `CONFIG_MISSING` 异常（#3），导致进程以退出码 78 异常终止（#2）。
*   追踪数据（#4）与日志证据高度一致，且应用返回了明确的业务错误码和模式标识（`config_missing_exit`），强有力地证明了该异常是由应用层面的配置缺失直接触发的，而非底层 K8s 调度或网络故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (CONFIG_MISSING) → 启动逻辑异常 → 容器退出码 78 → CrashLoopBackOff
```

### 根因结论

**已确认的直接原因**：
Pod 反复重启的直接原因是应用启动逻辑中的配置校验失败。Kubernetes 记录显示容器以退出码 `78` 终止（#2），日志（#3）与追踪（#4）明确记录了一个名为 `CONFIG_MISSING` 的异常事件以及 `aiops.observed_mode: config_missing_exit` 模式。应用启动失败导致 Pod 无法就绪（#1）。

**未确认的根因（证据不足）**：
具体的缺失配置源（如缺失的 ConfigMap、环境变量或文件）尚未确认。
*   日志（#3）仅报告了 `CONFIG_MISSING` 这一通用业务错误模式，未指出具体是哪一个键值（key）或配置项丢失。
*   追踪（#4）虽然定位到异常发生在 `GET /work` 请求的处理流程中，但并未提供应用内部的具体报错堆栈或配置查找路径。
*   输入未提供具体的 Pod 定义（Manifest）以供比对，也未提取到与 `CONFIG_MISSING` 直接关联的具体资源引用证据。因此，无法断定是配置注入错误、启动脚本缺陷还是外部依赖配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.9s
├─ 并发证据采集: 64.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 64.1s (Evidence 53.3s, RCA 10.6s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
