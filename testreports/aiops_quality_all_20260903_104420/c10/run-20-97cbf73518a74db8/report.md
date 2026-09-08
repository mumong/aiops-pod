## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，重启 21 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-79d9f8fd88-sbqvc` 状态 `CrashLoopBackOff`，重启 21 次 | 确认故障现象 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (重复 17 次) | 确认存活探针触发重启的根因触发点 |
| 3 | K8s Event | Kubernetes | Killing / Back-off restarting failed container (重复记录) | 确认 Kubelet 正在执行强制杀除与重启 |
| 4 | K8s State | Kubernetes | Container `app` 退出码 (Exit Code) 137 | 确认进程被 SIGKILL 强制终止 |
| 5 | Logging | Elasticsearch | 模式 `request completed` (HTTP 200, 路径 `/work`)，`allocated_mib` 在记录窗口内始终为 0 | 排除应用业务代码常规报错及日志可见的内存累积 |
| 6 | Tracing | Deepflow | 9 次 L7 Flow 显示 GET /work 响应 200 (耗时 18.7ms-46.0ms) | 佐证非健康检查路径的业务接口响应正常 |

**证据关联说明：**
*   证据 2 与证据 3 形成闭环：存活探针返回 500（证据 2）导致 Kubelet 发送信号（证据 3）。
*   证据 3 与证据 4 验证了终止方式：SIGKILL (137) 表明外部强杀，排除了进程正常退出的可能。
*   证据 5 与证据 6 形成排他性佐证：业务接口 `/work` 返回 200 且日志中内存始终为 0，结合 137 退出码，指向健康检查端点 `/health` 的独立异常或极短暂的瞬间崩溃（导致日志未记录）。

## 🎯 根因分析 · g1

### 因果链

```text
应用端点 /health 持续返回 HTTP 500 → Kubelet Liveness Probe 连续失败 → Kubelet 发送 SIGKILL 强制杀除容器 (Exit 137) → Pod 频繁重启导致 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用端点 /health 异常引发 Liveness Probe 失败。**

具体而言，Kubernetes 存活探针（Liveness Probe）在探测应用健康端点时持续收到 `HTTP 500` 错误（证据 #2），触发了 Kubernetes 的重置机制，Kubelet 随即发送 `SIGKILL` 信号终止容器（导致 Exit Code 137，证据 #4），进而引发 Pod 进入 `CrashLoopBackOff` 状态并循环重启 21 次（证据 #1）。

**证据支持：**
*   Kubernetes 事件明确指出“Liveness probe failed: HTTP probe failed with statuscode: 500”（证据 #2）。
*   Container 退出状态 `CrashLoopBackOff` 及 `Error`（Exit Code 137）证实了容器因探针失败被系统杀除（证据 #1, #4）。
*   日志与链路追踪显示应用的业务路径 `/work` 均返回 200 且无内存告警（证据 #5, #6），进一步将故障范围限定在非业务主路径的 `/health` 端点或该端点运行时的极短暂崩溃瞬间。

**未决事项：**
*   应用 `/health` 端点返回 500 的具体业务代码逻辑原因（日志中未捕获到崩溃瞬间的具体报错）。
*   是否存在极短瞬时的内存峰值导致 OOM（Exit 137 亦可能为 OOM Kill，但日志记录内存为 0 且无 OOMKilled 标记，当前证据倾向于非 OOM 或该指标在瞬间崩溃场景下不可见）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 17.7s
├─ 并发证据采集: 156.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 156.1s (Evidence 143.4s, RCA 12.5s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
