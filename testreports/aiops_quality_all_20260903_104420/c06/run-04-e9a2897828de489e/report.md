## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod `workload-7679bcf76-w9s9c` 处于 CrashLoopBackOff，容器 `app` 启动后立即以 Exit Code 2 崩溃，导致 Pod 无法 Ready。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-7679bcf76-w9s9c` 状态 Running，容器 `app` 等待原因 `CrashLoopBackOff`，最近退出码 `2`，重启次数 `6` | 确认应用反复启动失败，符合 CrashLoopBackOff 行为模式 |
| 2 | K8s Event | kubernetes | `Warning BackOff` (kubelet): `back-off 5m0s restarting failed container=app pod=workload-7679bcf76-w9s9c` (累计 21 次) | 证明 kubelet 按预期进行指数退避重启，确认 Pod 进入崩溃循环 |
| 3 | Logging | elasticsearch | 错误日志模式：`event: http_request, level: error, message: "runtime process exiting", http_status: 500, path: /work` (记录 4 次) | 提供应用崩溃的直接线索：进程在 HTTP 处理过程中因运行时错误退出 |
| 4 | Tracing | deepflow | L7 Flow 聚合：`GET /work` 响应 `500`，耗时 6330us - 17981us，与日志错误模式时间窗口重叠 | 从流量层确认了 HTTP 500 响应是伴随进程崩溃的必然现象 |
| 5 | Tracing | deepflow | L7 Flow 聚合：`GET /work` 响应 `200`，耗时 17719us - 26561us (记录 7 次) | 证明应用并非始终崩溃，存在成功处理请求的间歇期，排除了环境或网络导致的持续不可用 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `6`，`kube_pod_container_status_waiting_reason` 为 `CrashLoopBackOff` | 从监控指标侧面印证 K8s 状态中的重启计数与等待原因 |

**证据说明：**
K8s 事件与状态确认了 Pod 处于反复崩溃重启的 `CrashLoopBackOff` 阶段。日志中记录的 `runtime process exiting` 错误与 Tracing 中的 HTTP 500 响应相吻合，共同指向应用内部进程的非正常退出。同时，L7 Flow 中存在成功的 `200` 响应（耗时约 17ms-26ms），表明应用在重启后曾短暂恢复运行并成功处理请求，但随后再次因 `Exit Code 2` 退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动命令 `python3 /opt/aiops/server.py` 执行 → 运行时异常（Runtime Error）导致进程非正常退出 → Pod 状态变为 CrashLoopBackOff，容器不断重启 → 用户不可见健康服务，Pod 处于未就绪状态
```

### 根因结论

**已确认的根因：**
应用服务进程（容器 `app`）在启动或运行期间发生了运行时异常（Exit Code 2），导致进程退出。由于日志仅显示通用的 `"runtime process exiting"` 且无堆栈信息，具体是应用代码逻辑错误还是特定配置文件/依赖缺失，无法完全确定，但进程退出是导致 `CrashLoopBackOff` 的直接原因。
- 证据 1、2 证明了应用反复退出并被 Kubelet 判定为崩溃循环。
- 证据 3 和 4 证明了进程是在 HTTP 请求处理周期中因“运行时退出”而终止的。

**缺失的决定性事实：**
由于当前收集不到上一次崩溃容器的具体堆栈日志（如 `ep4-previous-logs` 工具尝试缺失或失败），无法精准定位触发 Exit Code 2 的具体应用层代码或配置细节。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 37.0s
├─ 并发证据采集: 52.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 52.8s (Evidence 41.6s, RCA 10.9s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-oomkilled
