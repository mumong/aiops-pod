## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器反复退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet | `container.waiting_reason=CrashLoopBackOff`, `container.last_terminated_reason=Error` | 确认 Pod `workload-7679bcf76-jwr8b` 处于反复重启状态 |
| 2 | K8s Event | kubelet | `BackOff restarting failed container app` (发生 203 次，持续 49 分钟) | 记录容器频繁非正常退出并由 kubelet 执行退避重启的实况 |
| 3 | K8s State | kubelet | `container.last_exit_code=2` (Container: app) | 确认应用程序进程以非零退出码 2 异常终止 |
| 4 | K8s State | kubelet | `restart_count=14` (Container: app) | 确认应用进程在短时间内已多次重启 |
| 5 | Logging | elasticsearch | `http_status: 500`, `message: "runtime process exiting"`, `path: /work` (发生 3 次) | 直接记录应用在处理 `/work` 请求时进程退出的底层日志 |
| 6 | Tracing | deepflow (L7 Flow) | HTTP GET `/work`, `response_code: 500` (发生 3 次), 关联 trace_ids `658aa169...` 等 | 证明 500 错误请求与日志记录的进程退出事件存在时间窗口上的关联 |
| 7 | K8s Config | kubelet | `container.resource_limit.memory=96Mi`, `container.resource_request.memory=24Mi` | 排除显式的内存资源硬限制作为直接退出原因的证据 |

**证据关系说明：**
Kubernetes 层面的 `CrashLoopBackOff` 和退出码 2 证实了 Pod 的崩溃现象 [证据 1, 2, 3]。Logging 中捕获到的 `"runtime process exiting"` 结合 Tracing 中的 HTTP 500 错误，揭示了崩溃的直接触发场景是处理特定的 `/work` 请求 [证据 5, 6]。内存配置限制较低，但并非导致进程逻辑错误退出的直接因素 [证据 7]。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 HTTP 请求到 /work → 内部运行时逻辑报错 → 进程无捕获退出 (exit code 2) → kubelet 检测到进程终止并触发 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用服务在运行时处理特定 HTTP 请求（`GET /work`）时发生逻辑错误，导致底层进程非正常终止（退出码 2），进而引发 Kubernetes 的 CrashLoopBackOff。

**证据支持**：
- **现象确认**：Kubernetes 事件和状态表明 `app` 容器频繁非正常退出 [证据 1, 2, 3]。
- **机制确认**：日志明确记录 `runtime process exiting`，Tracing 记录对应请求返回 500 错误 [证据 5, 6]，且 `allocated_mib` 始终为 0，排除了资源溢出触发的系统级 OOMKill [证据 5]。
- **不确定性**：具体的应用层异常原因（如 `NullPointerException` 或依赖缺失）未被日志或指标捕获 [证据 5, 6]，目前证据不足以确定代码中的确切出错行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.5s
├─ 并发证据采集: 67.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 67.8s (Evidence 58.5s, RCA 9.2s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
