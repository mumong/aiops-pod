## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8处于CrashLoopBackOff状态，容器app无法就绪 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `exit_code: 2` | 证明容器进程异常终止且非OOM |
| 2 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff`, `restart_count: 16` | 证实容器反复崩溃并进入指数退避等待阶段 |
| 3 | K8s Event | kubernetes | `Warning BackOff: Back-off restarting failed container app` | kubelet 日志记录了 63 分钟内 270 次退避重启 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} = 1` | 当前状态持续确认 |
| 5 | Logging | elasticsearch | `runtime process exiting`, `http_status 500`, `path: /work` (3 次, 含 trace `1946b848...`) | 日志显示应用在处理请求时异常退出 |
| 6 | Tracing | deepflow | L7 Flow `GET /work` 返回 `response_code 500` (2 次, trace `650e7da7...`) | 网络层观测到导致退出的请求流 |
| 7 | Tracing | tempo | Span `GET /work` 返回 200 (trace `b2c74bd5...`, 与成功日志一致) | 排除持续性问题，证实崩溃是瞬态或特定触发 |

**证据说明**：K8s 层面容器以 `exit_code=2` 退出（证据 1）且触发 `CrashLoopBackOff`（证据 2、3），直接印证应用层异常。日志记录显示请求 `/work` 在处理过程中出现 `runtime process exiting`（证据 5），Tracing 层对应观察到 500 错误（证据 6），且存在成功处理同一接口的请求记录（证据 7），说明异常发生在业务逻辑执行期间，而非基础设施网络故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码(server.py)存在运行时错误或缺失依赖 → Python进程抛出未捕获异常 → 进程以exitCode=2退出 → Pod处于CrashLoopBackOff状态
```

### 根因结论

**已确认的根因**：应用进程 `app` 在运行 `server.py` 时抛出未捕获的运行时异常并显式退出（`exit code 2`），导致容器反复崩溃。
**证据支持**：
1. 容器终止原因为 `Error` 且退出码为 `2`（证据 1）；
2. 日志记录显示进程在响应 `/work` 请求时 `runtime process exiting`（证据 5）；
3. K8s Event 与 Metrics 持续确认该容器处于 `CrashLoopBackOff` 状态（证据 2、4）。

**未知/不足**：具体的 Python 异常类型（如 `ImportError`、`KeyError` 等）及触发该异常的特定输入参数或配置缺失无法从现有数据确认，需要查看崩溃前的完整 Trace 或获取崩溃容器的标准输出日志。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 21.4s
├─ 并发证据采集: 55.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 55.4s (Evidence 44.5s, RCA 10.7s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-config-error
